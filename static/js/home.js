// Handle "Join Now" button for authenticated users
const joinNowBtn = document.getElementById('joinNowBtn');
if (joinNowBtn) {
    joinNowBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Show notification message
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show notification-item';
        notification.setAttribute('role', 'alert');
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            You are logged in. We are redirecting you to the Active Rounds page to play.
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Create or get notification container
        let notificationContainer = document.querySelector('.site-notifications');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'position-fixed top-0 start-0 p-3 site-notifications';
            notificationContainer.style.zIndex = '1040';
            notificationContainer.style.marginTop = '70px';
            document.body.appendChild(notificationContainer);
        }
        
        notificationContainer.appendChild(notification);
        
        // Redirect after a short delay
        setTimeout(() => {
            window.location.href = joinNowBtn.getAttribute('href');
        }, 3000);
    });
}

// AJAX comment submission
document.querySelectorAll('.comment-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(form);
        const card = form.closest('.recent-winner-card') || form.closest('.entry-card');
        let commentListContainer = card ? (card.querySelector('.comment-list') || card.querySelector('.list-group')) : null;
        if (!commentListContainer) {
            // As a fallback, try to find it by entry id
            const entryId = form.getAttribute('action').match(/(\d+)/)?.[1];
            const section = entryId ? document.getElementById('comments-section-' + entryId) : null;
            const fallbackContainer = section ? (section.querySelector('.comment-list') || section.querySelector('.list-group')) : null;
            if (fallbackContainer) {
                commentListContainer = fallbackContainer;
            } else {
                console.error('Comment list container not found');
                return;
            }
        }
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
                                    <button type="button" class="btn btn-sm btn-outline-secondary edit-comment-btn" 
                                        data-comment-id="${data.comment.id}" 
                                        data-edit-url="${data.comment.edit_url}">Edit</button>
                                    <button type="button" class="btn btn-sm btn-outline-danger delete-comment-btn" 
                                        data-comment-id="${data.comment.id}" 
                                        data-delete-url="${data.comment.delete_url}">Delete</button>
                                </div>
                            </div>
                            <p class="mb-0 comment-text">${data.comment.text}</p>
                            <div class="comment-edit-form" style="display: none;">
                                <textarea class="form-control form-control-sm mb-2" rows="2" 
                                id="edit_comment_${data.comment.id}" name="text" 
                                aria-label="Edit comment">${data.comment.text}</textarea>
                                <div class="d-flex gap-2">
                                    <button type="button" class="btn btn-sm btn-primary save-comment-btn">Save</button>
                                    <button type="button" class="btn btn-sm btn-secondary cancel-edit-btn">Cancel</button>
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

        if (!newText) {
            alert('Comment cannot be empty.');
            return;
        }

        // Get CSRF token
        const csrfTokenInput = commentItem.closest('.card-body').querySelector('[name="csrfmiddlewaretoken"]') || 
                               document.querySelector('[name="csrfmiddlewaretoken"]');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : document.querySelector('[name="csrfmiddlewaretoken"]')?.value;
        if (!csrfToken) {
            alert('CSRF token not found. Please refresh the page.');
            return;
        }

        // Get the edit URL from the edit button
        const editBtn = commentItem.querySelector('.edit-comment-btn');
        const editUrl = editBtn.getAttribute('data-edit-url');

        // Create URL-encoded form data
        const formData = new URLSearchParams();
        formData.append('text', newText);

        fetch(editUrl, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(JSON.stringify(data.errors) || 'Update failed');
                    }).catch(() => {
                        throw new Error('Update failed');
                    });
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

// Comment pagination AJAX
function initCommentPagination() {
    document.querySelectorAll('.comment-pagination').forEach(function(link) {
        link.onclick = function(e) {
            e.preventDefault();
            const entryId = this.dataset.entryId;
            const url = this.href + '&ajax=1';
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                const commentSection = document.getElementById('comments-section-' + entryId);
                if (commentSection) {
                    commentSection.innerHTML = html;
                    // Re-initialize pagination handlers for new links
                    initCommentPagination();
                }
            });
        };
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    initCommentPagination();
});
