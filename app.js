let generatedData = { html: '', css: '', js: '' };

document.getElementById('generate-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const prompt = document.getElementById('prompt').value;
    const btn = document.getElementById('generate-btn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');

    btnText.textContent = "جاري إنشاء الموقع...";
    spinner.classList.remove('hidden');
    btn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('prompt', prompt);

        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            generatedData = result;

            // Render preview inside iframe
            const iframe = document.getElementById('preview-iframe');
            const placeholder = document.getElementById('placeholder-state');

            placeholder.classList.add('hidden');
            iframe.classList.remove('hidden');

            const fullCode = `
                <!DOCTYPE html>
                <html>
                <head>
                    <style>${result.css}</style>
                </head>
                <body>
                    ${result.html}
                    <script>${result.js}</script>
                </body>
                </html>
            `;

            iframe.srcdoc = fullCode;

            // Populate hidden download form
            document.getElementById('download-html').value = result.html;
            document.getElementById('download-css').value = result.css;
            document.getElementById('download-js').value = result.js;

            // Show action panel
            document.getElementById('action-panel').classList.remove('hidden');
        } else {
            alert('حدث خطأ: ' + (result.error || 'فشل التوليد'));
        }
    } catch (err) {
        alert('حدث خطأ أثناء الاتصال بالسيرفر.');
        console.error(err);
    } finally {
        btnText.textContent = "🚀 إنشاء الموقع الآن";
        spinner.classList.add('hidden');
        btn.disabled = false;
    }
});

function setDevice(type) {
    const iframe = document.getElementById('preview-iframe');
    const btns = document.querySelectorAll('.device-toggle button');
    
    btns.forEach(b => b.classList.remove('active'));

    if (type === 'mobile') {
        iframe.classList.add('mobile');
        event.target.classList.add('active');
    } else {
        iframe.classList.remove('mobile');
        event.target.classList.add('active');
    }
}
