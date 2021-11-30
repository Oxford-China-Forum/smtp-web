// let myDropzone = new Dropzone("div#body-dropzone", { url: "/file/post"});

let bodyName, recipientsName;

document.getElementById('preview-form').addEventListener('submit', e => {
    e.preventDefault();
    console.log('submitted')

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
        bodyName = json.data.bodyName;
        recipientsName = json.data.recipientsName;
        console.log(bodyName, recipientsName);

        const parentContainer = document.getElementById('page-right-container');
        const iframe = document.createElement('iframe');
        iframe.setAttribute('src', `/preview?bodyName=${bodyName}&recipientsName=${recipientsName}`);
        iframe.style.width = '640px';
        iframe.style.height = '800px';
        parentContainer.innerHTML = '';
        parentContainer.appendChild(iframe);

        document.getElementById('submit-btn').innerHTML = '更新预览';
        document.getElementById('confirm-send-btn').removeAttribute('hidden');
    });
});

document.getElementById('confirm-send-btn').addEventListener('click', e => {
    fetch('/send', {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({bodyName: bodyName, recipientsName: recipientsName}),
    })
    .then(resp => resp.json())
    .then(json => console.log(json))
});
