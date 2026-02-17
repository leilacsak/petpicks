// AJAX comment submission
document.querySelectorAll('.comment-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const entryId = form.getAttribute('data-entry-id');
        const commentListContainer = form.closest('.card-body').querySelector('.comment-list');
        const textInput = form.querySelector('textarea');

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Create new comment HTML with Edit and Delete buttons
                    const commentHTML = `
                        <div class="list-group-item" data-comment-id="${data.comment.id}">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <strong>${data.comment.author}</strong>
                                <div class="d-flex gap-2 align-items-center">
                                    <small class="text-muted">${data.comment.created_at}</small>
                                    <button type="button" class="btn btn-sm btn-link edit-comment-btn" 
                                        data-comment-id="${data.comment.id}" 
                                        data-edit-url="${data.comment.edit_url}">Edit</button>
                                    <button type="button" class="btn btn-sm btn-link text-danger delete-comment-btn" 
                                        data-comment-id="${data.comment.id}" 
                                        data-delete-url="${data.comment.delete_url}">Delete</button>
                                </div>
                            </div>
                            <p class="mb-0 comment-text">${data.comment.text}</p>
                            <div class="comment-edit-form" style="display: none;">
                                <textarea class="form-control form-control-sm mb-2" rows="2">${data.comment.text}</textarea>
                                <div class="d-flex gap-2">
                                    <button class="btn btn-sm btn-primary save-comment-btn">Save</button>
                                    <button class="btn btn-sm btn-secondary cancel-edit-btn">Cancel</button>
                                </div>
                            </div>
                        </div>
                    `;

                    // Remove "No comments yet" message if it exists
                    const noCommentsMsg = commentListContainer.querySelector('.text-muted');
                    if (noCommentsMsg && noCommentsMsg.textContent === 'No comments yet.') {
                        noCommentsMsg.remove();
                    }

                    // Insert comment at the top of the list
                    commentListContainer.insertAdjacentHTML('afterbegin', commentHTML);

                    // Clear the form
                    textInput.value = '';
                    textInput.focus();
                } else {
                    console.error('Error posting comment:', data.errors);
                    alert('Error posting comment. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error posting comment. Please try again.');
            });
    });
});

// AJAX comment editing
document.addEventListener('click', function (e) {
    if (e.target.classList.contains('edit-comment-btn')) {
        e.preventDefault();

        const editBtn = e.target;
        const commentItem = editBtn.closest('.list-group-item');
        const commentText = commentItem.querySelector('.comment-text');
        const editForm = commentItem.querySelector('.comment-edit-form');

        commentText.style.display = 'none';
        editForm.style.display = 'block';
        editForm.querySelector('textarea').focus();
    }

    if (e.target.classList.contains('cancel-edit-btn')) {
        e.preventDefault();

        const cancelBtn = e.target;
        const commentItem = cancelBtn.closest('.list-group-item');
        const commentText = commentItem.querySelector('.comment-text');
        const editForm = commentItem.querySelector('.comment-edit-form');

        commentText.style.display = 'block';
        editForm.style.display = 'none';
    }

    if (e.target.classList.contains('save-comment-btn')) {
        e.preventDefault();

        const saveBtn = e.target;
        const commentItem = saveBtn.closest('.list-group-item');
        const editForm = commentItem.querySelector('.comment-edit-form');
        const textarea = editForm.querySelector('textarea');
        const newText = textarea.value.trim();
        const commentId = commentItem.getAttribute('data-comment-id');

        if (!newText) {
            alert('Comment cannot be empty.');
            return;
        }

        const formData = new FormData();
        formData.append('text', newText);
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // Get the edit URL from the edit button
        const editBtn = commentItem.querySelector('.edit-comment-btn');
        const editUrl = editBtn.getAttribute('data-edit-url');

        fetch(editUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update the comment text in the DOM
                    const commentText = commentItem.querySelector('.comment-text');
                    commentText.textContent = data.comment.text;

                    // Hide edit form and show comment text
                    commentText.style.display = 'block';
                    editForm.style.display = 'none';
                } else {
                    alert('Error updating comment. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error updating comment. Please try again.');
            });
    }

    if (e.target.classList.contains('delete-comment-btn')) {
        e.preventDefault();

        if (!confirm('Are you sure you want to delete this comment?')) {
            return;
        }

        const deleteBtn = e.target;
        const commentId = deleteBtn.getAttribute('data-comment-id');
        const deleteUrl = deleteBtn.getAttribute('data-delete-url');
        const commentItem = deleteBtn.closest('.list-group-item');

        const formData = new FormData();
        // Get CSRF token from the closest form or from the page
        const csrfTokenInput = commentItem.closest('.card-body').querySelector('[name="csrfmiddlewaretoken"]') || 
                               document.querySelector('[name="csrfmiddlewaretoken"]');
        if (csrfTokenInput) {
            formData.append('csrfmiddlewaretoken', csrfTokenInput.value);
        }

        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData,
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Get the comment list before removing the item
                    const commentList = commentItem.closest('.comment-list');
                    
                    // Remove the comment from the DOM
                    commentItem.remove();

                    // Check if comment list is now empty and show "No comments yet" message
                    if (commentList && commentList.children.length === 0) {
                        commentList.innerHTML = '<div class="list-group-item text-muted">No comments yet.</div>';
                    }
                } else {
                    alert('Error deleting comment. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error deleting comment. Please try again.');
            });
    }
});
