// let myDropzone = new Dropzone("div#body-dropzone", { url: "/file/post"});

let bodyName, recipientsName;
let readyToSend = false;
const statusText = document.getElementById('status-info');

function updateStatus(message, statusName) {
    statusName = statusName || 'light';
    statusText.className = '';
    statusText.classList.add('text-' + statusName);
    statusText.innerHTML = message;
}

function inputChanged() {
    if (readyToSend) {
        readyToSend = false;
        document.getElementById('confirm-send-btn').setAttribute('hidden', '');
    }
}

document.getElementById('preview-form').addEventListener('submit', e => {
    e.preventDefault();

    // Submit form and insert email preview
    const formData = new FormData(e.target);
    // formData.append('body', document.getElementById('bodyFile').files[0]);
    // formData.append('recipients', document.getElementById('recipientsFile').files[0]);

    fetch('/', {
        method: 'POST',
        body: formData,
    })
    .then(data => data.json())
    .then(json => {
        if (json.code !== 0) {
            updateStatus('缺少文件或空白标题', 'danger');
            return;
        }
        statusText.innerHTML = '';
        readyToSend = true;

        bodyName = json.data.bodyName;
        recipientsName = json.data.recipientsName;

        const parentContainer = document.getElementById('page-right-container');
        const iframe = document.createElement('iframe');
        iframe.setAttribute('src', `/preview?bodyName=${bodyName}&recipientsName=${recipientsName}`);
        iframe.style.width = '640px';
        iframe.style.height = '100vh';
        parentContainer.innerHTML = '';
        parentContainer.appendChild(iframe);

        document.getElementById('submit-btn').innerHTML = '更新预览';
        document.getElementById('confirm-send-btn').removeAttribute('hidden');
    });
});

document.getElementById('confirm-send-btn').addEventListener('click', e => {
    if (!confirm('是否确定开始批量发送邮件？这一操作无法中断。')) return;
    updateStatus('正在发送……');
    document.querySelectorAll('#preview-form button').forEach(el => el.setAttribute('disabled', ''));
    const subject = document.getElementById('subjectInput').value;
    fetch('/send', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({subject: subject, bodyName: bodyName, recipientsName: recipientsName}),
    })
    .then(resp => resp.json())
    .then(json => {
        console.log(json);
        document.querySelectorAll('#preview-form button').forEach(el => el.removeAttribute('disabled'));
        if (json.code === 0) {
            document.getElementById('confirm-send-btn').setAttribute('hidden', '');
            updateStatus('发送成功', 'success');
        } else {
            updateStatus('发送失败', 'danger');
        }
    })
});

document.querySelectorAll('#preview-form input').forEach(el => {
    el.addEventListener('change', inputChanged);
    el.addEventListener('input', inputChanged);
});
