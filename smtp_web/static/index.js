// let myDropzone = new Dropzone("div#body-dropzone", { url: "/file/post"});

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
    .then(data => {
        console.log(data);
        const iframe = document.createElement('iframe');
        iframe.setAttribute('src', '/preview');
        iframe.style.width = '640px';
        iframe.style.height = '800px';
        document.getElementById('page-right-container').appendChild(iframe);
    })
});
