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
  const cameraFileInput = document.getElementById('cameraFileInput');
  const galleryFileInput = document.getElementById('galleryFileInput');
  const cameraBtn = document.getElementById('cameraTriggerBtn');
  const galleryBtn = document.getElementById('galleryTriggerBtn');
  const dropzone = document.getElementById('imageDropzone');
  const imagePreview = document.getElementById('imagePreview');
  const dropzonePrompt = document.getElementById('dropzonePrompt');
  const compressionNotice = document.getElementById('compressionNotice');
  const removePhotoBtn = document.getElementById('removePhotoBtn');
  const captionTextarea = document.getElementById('captionTextarea');
  const submitBtn = document.getElementById('submitBtn');
  const successBanner = document.getElementById('successBanner');

  let currentProcessedFile = null;

  // 點擊「📸 現場拍照」按鈕
  if (cameraBtn && cameraFileInput) {
    cameraBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      cameraFileInput.click();
    });
  }

  // 點擊「🖼️ 從相簿選取」按鈕
  if (galleryBtn && galleryFileInput) {
    galleryBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      galleryFileInput.click();
    });
  }

  // 點擊上傳區外圍空白處（若尚未選擇照片），預設開啟相簿
  if (dropzone) {
    dropzone.addEventListener('click', (e) => {
      if (e.target.closest('#cameraTriggerBtn') || e.target.closest('#galleryTriggerBtn') || e.target.closest('#removePhotoBtn')) {
        return;
      }
      if (!currentProcessedFile && galleryFileInput) {
        galleryFileInput.click();
      }
    });
  }

  // 處理照片選取後的即時預覽與壓縮
  async function handleSelectedFile(file) {
    if (!file) return;

    showInstantPreview(file);

    if (compressionNotice) {
      compressionNotice.style.display = 'block';
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = '照片最佳化中... ⏳';
    }

    try {
      // 前端智慧壓縮：將相簿 20~40MB 巨大照片縮至 ~400KB，徹底消除 Failed to fetch 逾時崩潰
      currentProcessedFile = await compressImage(file, 1600, 1600, 0.82);
    } catch (err) {
      console.warn('前端壓縮失敗:', err);
      // 若原檔大於 12MB 且前端無法壓縮，提醒使用者
      if (file.size > 12 * 1024 * 1024) {
        alert('此相簿照片原始檔案過大（超過 12MB）且格式無法在瀏覽器中壓縮，請改用現場拍照或選擇一般 JPG/PNG 照片！');
        currentProcessedFile = null;
        if (removePhotoBtn) removePhotoBtn.click();
        return;
      }
      currentProcessedFile = file;
    } finally {
      if (compressionNotice) {
        compressionNotice.style.display = 'none';
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '分享';
      }
    }
  }

  if (cameraFileInput) {
    cameraFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleSelectedFile(e.target.files[0]);
      }
    });
  }

  if (galleryFileInput) {
    galleryFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleSelectedFile(e.target.files[0]);
      }
    });
  }

  let activePreviewUrl = null;

  // 即時預覽照片 (使用 URL.createObjectURL 避免 30MB base64 字串引發記憶體耗盡)
  function showInstantPreview(file) {
    if (activePreviewUrl) {
      URL.revokeObjectURL(activePreviewUrl);
    }
    activePreviewUrl = URL.createObjectURL(file);
    imagePreview.src = activePreviewUrl;
    imagePreview.style.display = 'block';
    dropzonePrompt.style.display = 'none';
    if (removePhotoBtn) removePhotoBtn.style.display = 'inline-flex';
  }

  // 移除/重新選擇照片
  if (removePhotoBtn) {
    removePhotoBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      currentProcessedFile = null;
      if (activePreviewUrl) {
        URL.revokeObjectURL(activePreviewUrl);
        activePreviewUrl = null;
      }
      if (cameraFileInput) cameraFileInput.value = '';
      if (galleryFileInput) galleryFileInput.value = '';
      if (fileInput) fileInput.value = '';
      imagePreview.src = '';
      imagePreview.style.display = 'none';
      dropzonePrompt.style.display = 'flex';
      removePhotoBtn.style.display = 'none';
      if (compressionNotice) compressionNotice.style.display = 'none';
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = '分享';
      }
    });
  }

  const previewWrapper = document.getElementById('captionPreviewWrapper');
  const livePreview = document.getElementById('captionLivePreview');

  function updateLivePreview() {
    if (!captionTextarea) return;
    const val = captionTextarea.value;
    if (val.trim()) {
      if (previewWrapper) previewWrapper.style.display = 'block';
      if (livePreview) livePreview.innerHTML = formatCaptionHashtags(val);
    } else {
      if (previewWrapper) previewWrapper.style.display = 'none';
      if (livePreview) livePreview.innerHTML = '';
    }
  }

  if (captionTextarea) {
    captionTextarea.addEventListener('input', updateLivePreview);
  }

  // 快捷 Hashtag 標籤點擊
  const pillBtns = document.querySelectorAll('.pill-btn');
  pillBtns.forEach(pill => {
    pill.addEventListener('click', () => {
      const tag = pill.getAttribute('data-tag');
      if (captionTextarea) {
        captionTextarea.value = (captionTextarea.value.trim() + ' ' + tag).trim() + ' ';
        captionTextarea.focus();
        updateLivePreview();
      }
    });
  });

  // AJAX 異步發文提交
  postForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentProcessedFile) {
      alert('請先選擇相簿照片或拍攝一張照片！');
      return;
    }

    const formData = new FormData(postForm);
    // 加入前端最佳化後的高品質相片
    formData.set('image', currentProcessedFile, currentProcessedFile.name || 'upload.jpg');

    submitBtn.disabled = true;
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '發布中... ⏳';

    try {
      const response = await fetch('/api/posts', {
        method: 'POST',
        body: formData
      });

      let data;
      try {
        data = await response.json();
      } catch (jsonErr) {
        if (response.status === 413) {
          throw new Error('照片檔案過大（超過限制），請選擇較小尺寸的照片！');
        } else {
          throw new Error(`伺服器異常 (狀態碼: ${response.status})，請確認連線或稍後再試。`);
        }
      }

      if (!response.ok || !data.success) {
        alert(data && data.error ? data.error : '貼文發布失敗，請稍後重試。');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        return;
      }

      // 發布成功
      if (successBanner) {
        successBanner.style.display = 'block';
        successBanner.scrollIntoView({ behavior: 'smooth' });
      }

      postForm.reset();
      currentProcessedFile = null;
      if (activePreviewUrl) {
        URL.revokeObjectURL(activePreviewUrl);
        activePreviewUrl = null;
      }
      if (cameraFileInput) cameraFileInput.value = '';
      if (galleryFileInput) galleryFileInput.value = '';
      imagePreview.style.display = 'none';
      dropzonePrompt.style.display = 'flex';
      if (removePhotoBtn) removePhotoBtn.style.display = 'none';
      if (previewWrapper) previewWrapper.style.display = 'none';
      
      submitBtn.textContent = '已發布！✨';
      setTimeout(() => {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }, 2000);

    } catch (err) {
      console.error('上傳錯誤:', err);
      alert(err.message || '上傳發生錯誤，請檢查網路連線或稍後重試。');
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  });
}

// 前端 Canvas 自動等比例縮圖與 JPEG 壓縮 (支援 createImageBitmap 與 ObjectURL 零記憶體暴增)
function compressImage(file, maxWidth = 1600, maxHeight = 1600, quality = 0.82) {
  return new Promise((resolve, reject) => {
    if (!file || !file.type || file.type.includes('svg') || file.type.includes('gif')) {
      return resolve(file);
    }

    // 優先使用硬體解碼器 createImageBitmap (最快、最省記憶體)
    if (typeof createImageBitmap === 'function') {
      createImageBitmap(file).then((bitmap) => {
        try {
          let { width, height } = bitmap;
          if (width > maxWidth || height > maxHeight) {
            if (width / height > maxWidth / maxHeight) {
              height = Math.round((height * maxWidth) / width);
              width = maxWidth;
            } else {
              width = Math.round((width * maxHeight) / height);
              height = maxHeight;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(bitmap, 0, 0, width, height);
          bitmap.close();

          canvas.toBlob((blob) => {
            if (blob && blob.size < file.size) {
              const fileName = (file.name || 'photo').replace(/\.[^/.]+$/, '') + '.jpg';
              resolve(new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() }));
            } else {
              resolve(file);
            }
          }, 'image/jpeg', quality);
        } catch (canvasErr) {
          bitmap.close();
          fallbackImageCompress(file, maxWidth, maxHeight, quality, resolve, reject);
        }
      }).catch(() => {
        fallbackImageCompress(file, maxWidth, maxHeight, quality, resolve, reject);
      });
      return;
    }

    fallbackImageCompress(file, maxWidth, maxHeight, quality, resolve, reject);
  });
}

function fallbackImageCompress(file, maxWidth, maxHeight, quality, resolve, reject) {
  const objectUrl = URL.createObjectURL(file);
  const img = new Image();

  img.onload = () => {
    URL.revokeObjectURL(objectUrl);
    try {
      let width = img.naturalWidth || img.width;
      let height = img.naturalHeight || img.height;

      if (width > maxWidth || height > maxHeight) {
        if (width / height > maxWidth / maxHeight) {
          height = Math.round((height * maxWidth) / width);
          width = maxWidth;
        } else {
          width = Math.round((width * maxHeight) / height);
          height = maxHeight;
        }
      }

      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0, width, height);

      canvas.toBlob((blob) => {
        if (blob && blob.size < file.size) {
          const fileName = (file.name || 'photo').replace(/\.[^/.]+$/, '') + '.jpg';
          resolve(new File([blob], fileName, { type: 'image/jpeg', lastModified: Date.now() }));
        } else {
          resolve(file);
        }
      }, 'image/jpeg', quality);
    } catch (e) {
      resolve(file);
    }
  };

  img.onerror = () => {
    URL.revokeObjectURL(objectUrl);
    reject(new Error('瀏覽器無法解析此相片格式'));
  };

  img.src = objectUrl;
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

  const VERIFIED_BADGE_SVG = `<svg class="verified-badge" viewBox="0 0 24 24" aria-label="官方認證" title="官方認證"><path fill="#0095f6" d="M22.5 12.5c0-1.58-.875-2.95-2.148-3.6.154-.435.238-.905.238-1.4 0-2.21-1.79-4-4-4-.495 0-.965.084-1.4.238C14.55 2.475 13.18 1.6 11.6 1.6c-1.58 0-2.95.875-3.6 2.148-.435-.154-.905-.238-1.4-.238-2.21 0-4 1.79-4 4 0 .495.084.965.238 1.4C1.575 9.55.7 10.92.7 12.5c0 1.58.875 2.95 2.148 3.6-.154.435-.238.905-.238 1.4 0 2.21 1.79 4 4 4 .495 0 .965-.084 1.4-.238 1.55 1.273 2.92 2.148 4.5 2.148 1.58 0 2.95-.875 3.6-2.148.435.154.905.238 1.4.238 2.21 0 4-1.79 4-4 0-.495-.084-.965-.238-1.4 1.273-.65 2.148-2.02 2.148-3.6zm-12.87 3.9l-4.13-4.13 1.41-1.41 2.72 2.72 6.59-6.59 1.41 1.41-8 8z"/></svg>`;

  if (modalImg) modalImg.src = post.image_url;
  if (modalAvatar) modalAvatar.src = post.character_avatar;
  if (modalName) modalName.innerHTML = `${post.character_name} ${VERIFIED_BADGE_SVG}`;
  if (modalHandle) modalHandle.textContent = post.character_handle;
  if (modalCaption) modalCaption.innerHTML = post.caption ? formatCaptionHashtags(post.caption) : '未輸入內文。';
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

/* --- Hashtag 自動高亮格式化與安全轉義 --- */
function formatCaptionHashtags(text) {
  if (!text) return '';
  const escaped = escapeHtml(text);
  // 將 # 開頭的中文、英文、數字、底線標籤轉為藍色 .hashtag 元素
  return escaped.replace(/(#[\u4e00-\u9fa5a-zA-Z0-9_]+)/g, '<span class="hashtag">$1</span>');
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
}
