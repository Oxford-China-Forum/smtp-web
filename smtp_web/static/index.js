// let myDropzone = new Dropzone("div#body-dropzone", { url: "/file/post"});

let bodyName, recipientsName, attachments;
let readyToSend = false;
const statusText = document.getElementById('status-info');
const socket = io();

function updateStatus(message, statusName) {
    statusName = statusName || 'light';
    statusText.className = '';
    statusText.classList.add('text-' + statusName);
    statusText.innerHTML = message;
}

function inputChanged(e) {
    // if (e.target.id == 'attachments') return;
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
            updateStatus(json.message, 'danger');
            return;
        }
        updateStatus('');
        readyToSend = true;

        bodyName = json.data.bodyName;
        recipientsName = json.data.recipientsName;
        attachments = json.data.attachments;

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
    updateStatus('开始发送……');
    document.querySelectorAll('#preview-form button').forEach(el => el.setAttribute('disabled', ''));
    const subject = document.getElementById('subjectInput').value;
    const data = {subject: subject, bodyName: bodyName, recipientsName: recipientsName, attachments: attachments};

    // Use SocketIO instead of fetch to communicate
    socket.emit('send', data);
});

document.querySelectorAll('#preview-form input').forEach(el => {
    el.addEventListener('change', inputChanged);
    el.addEventListener('input', inputChanged);
});

socket.on('message', (data) => {
    updateStatus(data.message, data.type);
});

socket.on('end', () => {
    document.querySelectorAll('#preview-form button').forEach(el => el.removeAttribute('disabled'));
    document.getElementById('confirm-send-btn').setAttribute('hidden', '');
});
