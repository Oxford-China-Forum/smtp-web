// let myDropzone = new Dropzone("div#body-dropzone", { url: "/file/post"});

document.getElementById('preview-form').addEventListener('submit', e => {
    const iframe = document.createElement('iframe');
    iframe.setAttribute('src', '/preview');
    iframe.style.width = "640px";
    iframe.style.height = "480px";
    document.body.appendChild(iframe);
});
