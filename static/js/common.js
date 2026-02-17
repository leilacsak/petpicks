// Image modal functionality - available on all pages
document.querySelectorAll('.winner-image').forEach(function (img) {
    img.addEventListener('click', function () {
        const fullImageUrl = this.getAttribute('data-full-image');
        const modalImage = document.getElementById('modalImage');
        const imageModal = new bootstrap.Modal(document.getElementById('imageModal'));

        modalImage.src = fullImageUrl;
        imageModal.show();
    });
});
