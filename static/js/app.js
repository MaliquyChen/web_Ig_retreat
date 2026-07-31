/* Instagram 活動互動系統 前端動態邏輯 (中文版) */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initPostForm();
  initScreenFeed();
  initModal();
});

/* --- 深淺色主題切換 --- */
function initTheme() {
  const themeToggle = document.getElementById('themeToggleBtn');
  const storedTheme = localStorage.getItem('ig_event_theme') || 'dark';
  
  document.documentElement.setAttribute('data-theme', storedTheme);
  updateThemeIcon(storedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('ig_event_theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }
}

function updateThemeIcon(theme) {
  const iconSpan = document.getElementById('themeIcon');
  if (iconSpan) {
    iconSpan.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
}

/* --- 手機發文表單邏輯 (/post) --- */
function initPostForm() {
  const postForm = document.getElementById('igPostForm');
  if (!postForm) return;

  const fileInput = document.getElementById('imageFileInput');
  const dropzone = document.getElementById('imageDropzone');
  const imagePreview = document.getElementById('imagePreview');
  const dropzonePrompt = document.getElementById('dropzonePrompt');
  const removePhotoBtn = document.getElementById('removePhotoBtn');
  const captionTextarea = document.getElementById('captionTextarea');
  const submitBtn = document.getElementById('submitBtn');
  const successBanner = document.getElementById('successBanner');

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        showPreview(file);
      }
    });
  }

  function showPreview(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      imagePreview.style.display = 'block';
      dropzonePrompt.style.display = 'none';
      if (removePhotoBtn) removePhotoBtn.style.display = 'flex';
    };
    reader.readAsDataURL(file);
  }

  if (removePhotoBtn) {
    removePhotoBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.value = '';
      imagePreview.src = '';
      imagePreview.style.display = 'none';
      dropzonePrompt.style.display = 'flex';
      removePhotoBtn.style.display = 'none';
    });
  }

  // 快捷 Hashtag 標籤點擊
  const pillBtns = document.querySelectorAll('.pill-btn');
  pillBtns.forEach(pill => {
    pill.addEventListener('click', () => {
      const tag = pill.getAttribute('data-tag');
      if (captionTextarea) {
        captionTextarea.value = (captionTextarea.value.trim() + ' ' + tag).trim() + ' ';
        captionTextarea.focus();
      }
    });
  });

  // AJAX 異步發文提交
  postForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!fileInput.files || fileInput.files.length === 0) {
      alert('請先選擇或拍攝一張照片！');
      return;
    }

    const formData = new FormData(postForm);
    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '發布中... ⏳';

    try {
      const response = await fetch('/api/posts', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (data.success) {
        if (successBanner) {
          successBanner.style.display = 'block';
          successBanner.scrollIntoView({ behavior: 'smooth' });
        }

        postForm.reset();
        imagePreview.style.display = 'none';
        dropzonePrompt.style.display = 'flex';
        if (removePhotoBtn) removePhotoBtn.style.display = 'none';
        
        submitBtn.textContent = '已發布！✨';
        setTimeout(() => {
          submitBtn.disabled = false;
          submitBtn.textContent = originalText;
        }, 2000);
      } else {
        alert(data.error || '貼文發布失敗，請稍後重試。');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    } catch (err) {
      console.error('上傳錯誤:', err);
      alert('上傳發生錯誤，請檢查網路連線。');
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}

/* --- 大螢幕輪詢與即時更新 (/screen) --- */
let currentPostsData = [];
let pollingInterval = null;

function initScreenFeed() {
  const postsGrid = document.getElementById('postsGrid');
  if (!postsGrid) return;

  const characterId = postsGrid.getAttribute('data-character-id');

  fetchPosts(characterId);

  // 每 10 秒自動輪詢更新
  pollingInterval = setInterval(() => {
    fetchPosts(characterId, true);
  }, 10000);
}

async function fetchPosts(characterId, isBackgroundRefresh = false) {
  const postsGrid = document.getElementById('postsGrid');
  if (!postsGrid) return;

  try {
    let url = '/api/posts';
    if (characterId && characterId !== 'all') {
      url += `?character_id=${characterId}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    if (data.success) {
      const newIds = data.posts.map(p => p.id).join(',');
      const oldIds = currentPostsData.map(p => p.id).join(',');

      currentPostsData = data.posts;
      updatePostCount(data.posts.length);

      if (newIds !== oldIds || !isBackgroundRefresh) {
        renderPostsGrid(data.posts);
      }
    }
  } catch (err) {
    console.error('獲取貼文列表失敗:', err);
  }
}

function updatePostCount(count) {
  const postCountEl = document.getElementById('statPostCount');
  if (postCountEl) {
    postCountEl.textContent = count;
  }
}

function renderPostsGrid(posts) {
  const postsGrid = document.getElementById('postsGrid');
  if (!postsGrid) return;

  if (posts.length === 0) {
    postsGrid.innerHTML = `
      <div class="empty-state">
        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 9a2 2 0 012-2h0.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p style="font-size: 1.1rem; font-weight: 600;">尚無貼文</p>
        <p style="font-size: 0.9rem;">掃描角色 QR Code 來發布第一張活動照片！</p>
      </div>
    `;
    return;
  }

  postsGrid.innerHTML = posts.map(post => `
    <div class="grid-item" onclick="openModal(${post.id})">
      <img src="${post.image_url}" alt="角色貼文照片" loading="lazy" />
      <div class="grid-overlay">
        <div class="overlay-stat">
          <svg width="20" height="20" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
          <span id="gridLikeCount-${post.id}">${post.likes}</span>
        </div>
      </div>
    </div>
  `).join('');
}

/* --- 放大燈箱控制 (LIGHTBOX MODAL) --- */
let activeModalPostId = null;

function initModal() {
  const modalOverlay = document.getElementById('imageModal');
  const closeBtn = document.getElementById('modalCloseBtn');

  if (closeBtn && modalOverlay) {
    closeBtn.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => {
      if (e.target === modalOverlay) {
        closeModal();
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modalOverlay.classList.contains('open')) {
        closeModal();
      }
    });
  }
}

window.openModal = function(postId) {
  const post = currentPostsData.find(p => p.id === postId);
  if (!post) return;

  activeModalPostId = postId;
  const modalOverlay = document.getElementById('imageModal');
  const modalImg = document.getElementById('modalImage');
  const modalAvatar = document.getElementById('modalAvatar');
  const modalName = document.getElementById('modalName');
  const modalHandle = document.getElementById('modalHandle');
  const modalCaption = document.getElementById('modalCaption');
  const modalLikes = document.getElementById('modalLikesCount');
  const modalTime = document.getElementById('modalTime');
  const modalLikeBtn = document.getElementById('modalLikeBtn');
  const modalDeleteBtn = document.getElementById('modalDeleteBtn');

  if (modalImg) modalImg.src = post.image_url;
  if (modalAvatar) modalAvatar.src = post.character_avatar;
  if (modalName) modalName.textContent = post.character_name;
  if (modalHandle) modalHandle.textContent = post.character_handle;
  if (modalCaption) modalCaption.textContent = post.caption || '未輸入內文。';
  if (modalLikes) modalLikes.textContent = post.likes;
  if (modalTime) modalTime.textContent = formatDate(post.created_at);

  if (modalLikeBtn) {
    modalLikeBtn.onclick = () => handleLikePost(postId);
  }

  if (modalDeleteBtn) {
    modalDeleteBtn.onclick = () => handleDeletePost(postId);
  }

  if (modalOverlay) modalOverlay.classList.add('open');
};

function closeModal() {
  const modalOverlay = document.getElementById('imageModal');
  if (modalOverlay) modalOverlay.classList.remove('open');
  activeModalPostId = null;
}

async function handleLikePost(postId) {
  try {
    const response = await fetch(`/api/posts/${postId}/like`, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      const modalLikes = document.getElementById('modalLikesCount');
      if (modalLikes) modalLikes.textContent = data.likes;

      const gridLikes = document.getElementById(`gridLikeCount-${postId}`);
      if (gridLikes) gridLikes.textContent = data.likes;

      const postObj = currentPostsData.find(p => p.id === postId);
      if (postObj) postObj.likes = data.likes;
    }
  } catch (err) {
    console.error('按讚失敗:', err);
  }
}

async function handleDeletePost(postId) {
  if (!confirm('確定要刪除這張貼文嗎？刪除後將無法復原。')) {
    return;
  }

  try {
    const response = await fetch(`/api/posts/${postId}`, {
      method: 'DELETE'
    });
    const data = await response.json();

    if (data.success) {
      closeModal();
      const postsGrid = document.getElementById('postsGrid');
      const characterId = postsGrid ? postsGrid.getAttribute('data-character-id') : 'all';
      fetchPosts(characterId, false);
    } else {
      alert(data.error || '刪除貼文失敗！');
    }
  } catch (err) {
    console.error('刪除貼文失敗:', err);
    alert('刪除請求發生錯誤，請檢查網路連線。');
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '剛剛';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '最近';
  return d.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' });
}
