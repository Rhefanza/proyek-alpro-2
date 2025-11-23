// Smooth scroll for nav and CTAs
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click', e=>{
    e.preventDefault();
    const id=a.getAttribute('href');
    const el=document.querySelector(id);
    if(el) el.scrollIntoView({behavior:'smooth',block:'start'});
  })
});

// Setup modal for Convert Image
function createModal(){
  const modal=document.createElement('div');modal.className='modal';
  modal.innerHTML=`<div class="dialog">
    <h3>Convert Image to CSV</h3>
    <p class="small">Upload a JPG/JPEG/PNG. This demo will create a placeholder CSV using the file name and a few mock rows.</p>
    <input type="file" id="imgfile" accept="image/*" />
    <div class="csv-preview" id="csvPreview" style="display:none"></div>
    <div style="margin-top:12px;text-align:right"><button id="closeModal" class="btn-ghost">Close</button></div>
  </div>`;
  document.body.appendChild(modal);

  modal.querySelector('#closeModal').addEventListener('click', ()=>modal.remove());
  modal.querySelector('#imgfile').addEventListener('change', handleFile);
}

function handleFile(e){
  const f=e.target.files[0];
  const preview=document.getElementById('csvPreview');
  if(!f) return;
  const rows=[['filename','rows_detected','note'],[f.name,3,'mock data - replace with OCR pipeline'],['row_1',123,'value'],['row_2',456,'value']];
  const csv=rows.map(r=>r.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(',')).join('\n');
  const blob=new Blob([csv],{type:'text/csv'});
  const url=URL.createObjectURL(blob);
  preview.style.display='block';
  preview.innerHTML=`<strong>Preview CSV</strong><pre style="white-space:pre-wrap">${csv}</pre>
    <p style="text-align:right"><a href="${url}" download="converted.csv" class="btn-ghost">Download CSV</a></p>`;
}

// Button hooks
const convertBtn=document.getElementById('convertBtn');
if(convertBtn) convertBtn.addEventListener('click', ()=>createModal());

const analyzeBtn=document.getElementById('analyzeBtn');
if(analyzeBtn) analyzeBtn.addEventListener('click', ()=>{
  document.querySelector('#analyze').scrollIntoView({behavior:'smooth',block:'start'});
});

// Accessibility: close modal with Esc
window.addEventListener('keydown', (e)=>{if(e.key==='Escape'){const m=document.querySelector('.modal'); if(m) m.remove();}});
