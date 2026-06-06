import csv
import json
from io import StringIO
from flask import Flask, render_template, request, jsonify
from models import db, Analysis
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///optimizer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'llmcostoptimizersecret'

db.init_app(app)
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

with app.app_context():
    db.create_all()

# ── Parsers ────────────────────────────────────────────
def parse_openai_bill(csv_content):
    lines  = csv_content.strip().split('\n')
    reader = csv.DictReader(lines)
    total, model_spending = 0.0, {}
    for row in reader:
        try:
            cost  = float(row.get('cost', 0))
            model = row.get('model', 'unknown')
            total += cost
            model_spending[model] = model_spending.get(model, 0) + cost
        except (ValueError, TypeError):
            continue
    return {'total': total, 'by_model': model_spending, 'provider': 'openai'}

def parse_anthropic_bill(csv_content):
    lines = csv_content.strip().split('\n')
    total, model_spending = 0.0, {}
    for line in lines[1:]:
        parts = line.split(',')
        if len(parts) >= 2:
            try:
                cost  = float(parts[-1].replace('$', '').strip())
                model = parts[0] if len(parts) > 0 else 'claude'
                total += cost
                model_spending[model] = model_spending.get(model, 0) + cost
            except (ValueError, IndexError):
                continue
    return {'total': total, 'by_model': model_spending, 'provider': 'anthropic'}

def parse_generic_bill(csv_content):
    """Fallback parser for any CSV with a cost/amount/price column."""
    lines  = csv_content.strip().split('\n')
    reader = csv.DictReader(lines)
    total, model_spending = 0.0, {}
    cost_keys  = ['cost', 'amount', 'price', 'total', 'charge']
    model_keys = ['model', 'service', 'name', 'product']
    fieldnames = [f.lower() for f in (reader.fieldnames or [])]

    cost_key  = next((k for k in cost_keys  if k in fieldnames), None)
    model_key = next((k for k in model_keys if k in fieldnames), None)

    for row in reader:
        lrow = {k.lower(): v for k, v in row.items()}
        try:
            if cost_key:
                cost = float(str(lrow.get(cost_key, 0)).replace('$', '').strip())
            else:
                nums = [float(v.replace('$','').strip())
                        for v in lrow.values()
                        if v.replace('$','').replace('.','').replace('-','').isdigit()]
                cost = nums[-1] if nums else 0
            model = lrow.get(model_key, 'unknown') if model_key else 'unknown'
            total += cost
            model_spending[model] = model_spending.get(model, 0) + cost
        except (ValueError, TypeError):
            continue
    return {'total': total, 'by_model': model_spending, 'provider': 'unknown'}

def detect_provider(csv_content):
    lower = csv_content.lower()
    if any(k in lower for k in ['gpt-4', 'gpt-3.5', 'gpt-4o', 'davinci', 'openai']):
        return 'openai'
    elif any(k in lower for k in ['claude', 'anthropic', 'haiku', 'sonnet', 'opus']):
        return 'anthropic'
    elif any(k in lower for k in ['gemini', 'google']):
        return 'google'
    elif any(k in lower for k in ['llama', 'groq', 'mixtral']):
        return 'groq'
    return 'unknown'

# ── Routes ─────────────────────────────────────────────
@app.route('/')
def index():
    analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(10).all()
    return render_template('index.html', analyses=analyses)

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        content  = file.read().decode('utf-8')
        provider = detect_provider(content)

        if provider == 'openai':
            data = parse_openai_bill(content)
        elif provider == 'anthropic':
            data = parse_anthropic_bill(content)
        else:
            data = parse_generic_bill(content)
            data['provider'] = provider

        # Build model breakdown text
        if data['by_model']:
            breakdown_text = '\n'.join(
                f"  - {model}: ${amount:.4f}"
                for model, amount in sorted(
                    data['by_model'].items(), key=lambda x: x[1], reverse=True
                )
            )
        else:
            breakdown_text = '  - No model breakdown available'

        prompt = f"""You are an expert LLM cost optimization consultant.

A user uploaded their LLM API bill. Here are the details:

Provider: {data['provider'].upper()}
Total Spent: ${data['total']:.4f}

Spending by Model:
{breakdown_text}

Please provide:
1. A brief assessment of their current spending pattern (2-3 sentences)
2. 4 specific, actionable cost-saving recommendations with estimated savings %
3. A priority action — the single most impactful change they can make today

Be concrete. Name specific cheaper models as alternatives. Give real percentage estimates.
Format clearly with numbered lists."""

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=1024,
            temperature=0.5
        )

        recommendations = response.choices[0].message.content

        analysis = Analysis(
            filename    = file.filename,
            total_spent = data['total'],
            provider    = data['provider'],
            raw_data    = json.dumps(data),
            analysis    = recommendations
        )
        db.session.add(analysis)
        db.session.commit()

        return jsonify({
            'success':         True,
            'analysis_id':     analysis.id,
            'total_spent':     round(data['total'], 4),
            'provider':        data['provider'],
            'breakdown':       data['by_model'],
            'recommendations': recommendations
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/analysis/<int:analysis_id>')
def get_analysis(analysis_id):
    analysis = Analysis.query.get(analysis_id)
    if not analysis:
        return jsonify({'error': 'Not found'}), 404
    raw = json.loads(analysis.raw_data or '{}')
    result = analysis.to_dict()
    result['breakdown'] = raw.get('by_model', {})
    return jsonify(result)

@app.route('/api/analyses')
def list_analyses():
    analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(20).all()
    return jsonify([a.to_dict() for a in analyses])

if __name__ == '__main__':
    app.run(debug=True, port=5007)