import os
import json
import pandas as pd
import threading
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

# --- IMPORT MODUL UTAMA KITA ---
import analysis_core
import image_processing  # File placeholder tim Anda (OCR)
import insight_engine    # File placeholder tim Anda (AI Insight)
import pdf_generator     # File generator PDF

# --- KONFIGURASI APLIKASI ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATABASE_FILE = f"sqlite:///{os.path.join(BASE_DIR, 'proyek.db')}"
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_FILE
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- MODEL DATABASE ---

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    columns_list = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, running, completed, failed
    
    # Input Parameters
    data_type = db.Column(db.String(50))
    y_var = db.Column(db.String(255))
    x_vars = db.Column(db.JSON)
    entity_col = db.Column(db.String(255), nullable=True)
    time_col = db.Column(db.String(255), nullable=True)
    
    # Outputs
    results = db.Column(db.Text, nullable=True)        # JSON Statistik
    interpretation = db.Column(db.Text, nullable=True) # Teks Insight
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

# --- WORKER THREAD (PROSES ANALISIS) ---

def run_analysis_worker(analysis_id):
    """Berjalan di background untuk menghitung statistik & generate insight."""
    with app.app_context():
        try:
            # 1. Ambil Data
            analysis = db.session.get(Analysis, analysis_id)
            dataset = db.session.get(Dataset, analysis.dataset_id)
            
            if not dataset: raise ValueError("Dataset not found")

            analysis.status = 'running'
            db.session.commit()

            # 2. Load File ke Pandas (Smart Loader)
            ext = dataset.file_path.rsplit('.', 1)[1].lower()
            df = None

            if ext == 'csv':
                try:
                    # Coba koma dulu
                    df = pd.read_csv(dataset.file_path, sep=',')
                    # Jika gagal pisah kolom (cuma 1 kolom), coba titik koma
                    if len(df.columns) < 2:
                        df = pd.read_csv(dataset.file_path, sep=';')
                except:
                    # Fallback ke engine python
                    df = pd.read_csv(dataset.file_path, sep=None, engine='python')
            
            elif ext in ['xlsx', 'xls']:
                df = pd.read_excel(dataset.file_path)
            
            else:
                raise ValueError("File gambar tidak bisa dianalisis langsung. Gunakan fitur Convert Image dulu.")

            # Normalisasi nama kolom (huruf kecil, tanpa spasi)
            df.columns = df.columns.str.strip().str.lower()

            # 3. Jalankan Analisis Statistik (Analysis Core)
            json_res_string = analysis_core.run_analysis(
                df=df,
                y_var=analysis.y_var,
                x_vars=analysis.x_vars,
                data_type=analysis.data_type,
                entity_col=analysis.entity_col,
                time_col=analysis.time_col
            )
            
            # 4. Generate Insight (Insight Engine)
            # Ubah string JSON kembali ke Dict untuk dibaca Insight Engine
            res_dict = json.loads(json_res_string)
            insight_text = insight_engine.generate_insight(res_dict)
            
            # 5. Simpan Hasil
            analysis.results = json_res_string
            analysis.interpretation = insight_text
            analysis.status = 'completed'
            analysis.completed_at = datetime.utcnow()

        except Exception as e:
            analysis.status = 'failed'
            analysis.error_message = str(e)
            print(f"Worker Error: {e}")
        
        finally:
            db.session.commit()

# --- HALAMAN WEB (VIEW) ---

@app.route('/')
def landing_page():
    """Halaman Depan (Landing Page)"""
    return render_template('landing.html')

@app.route('/app')
def dashboard_page():
    """Halaman Utama Aplikasi (Upload -> Select -> Result)"""
    return render_template('dashboard.html')

@app.route('/convert')
def convert_page():
    """Halaman Konversi Gambar (OCR)"""
    return render_template('convert_image.html')

# --- API: DATASET & UPLOAD ---

@app.route('/datasets', methods=['POST'])
def upload_dataset():
    """Upload CSV/Excel untuk analisis langsung."""
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400
    
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    
    # Baca Kolom untuk Preview
    cols = []
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext in ['csv', 'xlsx', 'xls']:
        try:
            if ext == 'csv':
                df = pd.read_csv(path, sep=None, engine='python')
            else:
                df = pd.read_excel(path)
            
            df.columns = df.columns.str.strip().str.lower()
            cols = list(df.columns)
        except Exception as e:
            return jsonify({'error': f"Gagal membaca file: {str(e)}"}), 500
    
    # Simpan ke DB
    ds = Dataset(file_name=filename, file_path=path, columns_list=cols)
    db.session.add(ds)
    db.session.commit()
    
    return jsonify({
        'dataset_id': ds.id, 
        'file_name': ds.file_name, 
        'columns': cols, 
        'file_type': ext
    })

@app.route('/api/datasets/<int:id>', methods=['GET'])
def get_dataset_info(id):
    """API untuk mengambil info dataset (dipakai saat redirect dari Convert -> Dashboard)."""
    ds = db.session.get(Dataset, id)
    if not ds: return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'dataset_id': ds.id, 
        'file_name': ds.file_name, 
        'columns': ds.columns_list
    })

# --- API: IMAGE PROCESSING (OCR) ---

@app.route('/api/process-image', methods=['POST'])
def process_image_api():
    """Upload Gambar -> OCR -> Return Data Tabel."""
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    
    try:
        # Panggil Fungsi Tim OCR
        df = image_processing.process_image_to_data(path)
        
        # Simpan hasil OCR sebagai CSV baru agar bisa dianalisis
        csv_name = f"ocr_result_{datetime.now().strftime('%H%M%S')}.csv"
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_name)
        df.to_csv(csv_path, index=False)
        
        # Simpan ke DB
        ds = Dataset(file_name=f"OCR: {filename}", file_path=csv_path, columns_list=list(df.columns))
        db.session.add(ds)
        db.session.commit()
        
        return jsonify({
            'dataset_id': ds.id,
            'columns': list(df.columns),
            'data': df.head(10).to_dict(orient='records') # Preview 10 baris
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- API: ANALISIS ---

@app.route('/analyses', methods=['POST'])
def start_analysis():
    """Memulai request analisis baru."""
    data = request.json
    
    # Validasi dasar
    if not data.get('dataset_id') or not data.get('y_var'):
        return jsonify({'error': 'Data tidak lengkap'}), 400

    analysis = Analysis(
        dataset_id=data['dataset_id'],
        data_type=data['data_type'],
        y_var=data['y_var'],
        x_vars=data['x_vars'],
        entity_col=data.get('entity_col'),
        time_col=data.get('time_col'),
        status='pending'
    )
    db.session.add(analysis)
    db.session.commit()
    
    # Jalankan di thread terpisah agar tidak blocking
    threading.Thread(target=run_analysis_worker, args=(analysis.id,)).start()
    
    return jsonify({'message': 'Started', 'analysis_id': analysis.id}), 202

@app.route('/analyses/<int:id>', methods=['GET'])
def get_analysis_result(id):
    """Polling status analisis."""
    a = db.session.get(Analysis, id)
    if not a: return jsonify({'error': 'Not found'}), 404
    
    response = {'status': a.status}
    
    if a.status == 'completed':
        response['results'] = json.loads(a.results)
        response['interpretation'] = a.interpretation
    elif a.status == 'failed':
        response['error'] = a.error_message
        
    return jsonify(response)

# --- API: PDF REPORT ---

@app.route('/api/download-pdf/<int:id>')
def download_pdf(id):
    """Generate dan download PDF."""
    a = db.session.get(Analysis, id)
    if not a or a.status != 'completed': return "Analysis not ready", 404
    
    pdf_filename = f"report_{id}.pdf"
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    
    try:
        # Siapkan data untuk PDF
        results_dict = json.loads(a.results)
        # Masukkan insight ke dict agar tercetak
        if a.interpretation:
            results_dict['interpretation'] = a.interpretation
            
        pdf_generator.generate_pdf_report(results_dict, pdf_path)
        
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        return f"Error generating PDF: {e}", 500

# --- MAIN ENTRY POINT ---

if __name__ == '__main__':
    # Buat tabel database jika belum ada
    with app.app_context():
        db.create_all()
    
    print("🚀 Server EconoVision berjalan di http://127.0.0.1:5000")
    app.run(debug=True)