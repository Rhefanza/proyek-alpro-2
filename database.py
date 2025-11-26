# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Buat instance SQLAlchemy yang akan dihubungkan ke aplikasi Flask
db = SQLAlchemy()

class Dataset(db.Model):
    """
    Model untuk menyimpan metadata file yang diunggah.
    """
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False, unique=True)
    columns_list = db.Column(db.JSON, nullable=True) # Menyimpan daftar kolom sebagai JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi: Satu Dataset bisa memiliki banyak Analisis
    analyses = db.relationship('Analysis', backref='dataset', lazy=True)

    def __repr__(self):
        return f"<Dataset {self.id}: {self.file_name}>"

class Analysis(db.Model):
    """
    Model untuk menyimpan status dan hasil dari setiap pekerjaan analisis.
    """
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    
    # Status pekerjaan: 'pending', 'running', 'completed', 'failed'
    status = db.Column(db.String(50), nullable=False, default='pending')
    
    # Input dari user
    data_type = db.Column(db.String(50))
    y_var = db.Column(db.String(255))
    x_vars = db.Column(db.JSON) # Menyimpan list [x1, x2, ...]
    entity_col = db.Column(db.String(255), nullable=True)
    time_col = db.Column(db.String(255), nullable=True)
    
    # Output dari analysis_core.py (disimpan sebagai string JSON besar)
    results = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Analysis {self.id} (Status: {self.status})>"