from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Analysis(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    filename    = db.Column(db.String(255), nullable=False)
    total_spent = db.Column(db.Float, nullable=False)
    provider    = db.Column(db.String(50))
    raw_data    = db.Column(db.Text)
    analysis    = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':          self.id,
            'filename':    self.filename,
            'total_spent': self.total_spent,
            'provider':    self.provider,
            'analysis':    self.analysis,
            'created_at':  self.created_at.isoformat()
        }