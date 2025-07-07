// settings_script.js
// Country dropdown and user profile update logic for settings page

const countryBtn = document.querySelector('.country-btn');
const countryDropdown = document.getElementById('country-dropdown');
const countryList = document.getElementById('country-list');
const countrySearch = document.getElementById('country-search');
const selectedCountrySpan = document.getElementById('selected-country');

function populateCountries() {
  countryList.innerHTML = '';
  if (!window.ALL_COUNTRIES) return;
  window.ALL_COUNTRIES.forEach(({ name, flag }) => {
    const div = document.createElement('div');
    div.className = 'country-option';
    div.innerHTML = `<span class="flag">${flag}</span> <span class="country-name">${name}</span>`;
    div.onclick = () => selectCountry(name);
    countryList.appendChild(div);
  });
}

// --- Modal Utility ---

// Attach all settings button actions based on order in DOM
window.addEventListener('DOMContentLoaded', function() {
  const settingBtns = document.querySelectorAll('.setting-btn.placeholder-btn');
  // Button order: [0] Profile Picture, [1] Username, [2] Terms, [3] Password
  if (settingBtns[0]) {
    // Profile Picture
    settingBtns[0].onclick = function() {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = async function(e) {
        const file = e.target.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('profile_pic', file);
        try {
          const res = await fetch('/api/user/upload_profile_pic', { method: 'POST', body: formData });
          const data = await res.json();
          if (data.success) {
            showToast('Profile photo updated!', 'success');
          } else {
            showToast('Failed to update photo', 'error');
          }
        } catch {
          showToast('Network error', 'error');
        }
      };
      input.click();
    };
  }
  if (settingBtns[1]) {
    // Username
    settingBtns[1].onclick = function() {
      createModal({
        title: 'Edit Username',
        inputType: 'text',
        inputPlaceholder: 'Enter new username',
        confirmText: 'Save',
        cancelText: 'Cancel',
        onConfirm: (username) => {
          if (!username) return;
          fetch('/api/user/update_username', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
          })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                showToast('Username updated!', 'success');
              } else {
                showToast('Failed to update username', 'error');
              }
            })
            .catch(() => showToast('Network error', 'error'));
        }
      });
    };
  }
  if (settingBtns[2]) {
    // Terms
    settingBtns[2].onclick = function() {
      createModal({
        title: 'Terms & Conditions',
        content: `<div class='lumon-terms-content'>
          <h3>Welcome to Lumon!</h3>
          <p>By using this app, you agree to the following terms:</p>
          <ul>
            <li><b>Privacy:</b> Your personal data is stored securely and never sold to third parties. You may delete your account at any time.</li>
            <li><b>Content:</b> You are responsible for the content you upload or generate. Do not upload illegal, offensive, or copyrighted material without permission.</li>
            <li><b>Usage:</b> You agree not to misuse the app, attempt unauthorized access, or disrupt service for others.</li>
            <li><b>Changes:</b> Lumon reserves the right to update these terms and will notify users of significant changes.</li>
            <li><b>Disclaimer:</b> This app is provided as-is, without warranties. Use at your own risk.</li>
          </ul>
          <p>Contact support for questions or concerns.</p>
        </div>`,
        confirmText: 'Close'
      });
    };
  }
  if (settingBtns[3]) {
    // Password
    settingBtns[3].onclick = function() {
      createModal({
        title: 'Change Password',
        confirmText: 'Save',
        cancelText: 'Cancel',
        inputs: [
          { type: 'password', placeholder: 'Enter old password' },
          { type: 'password', placeholder: 'Enter new password' }
        ],
        onConfirm: (oldPassword, newPassword) => {
          if (!oldPassword || !newPassword) {
            showToast('Both fields are required', 'error');
            return;
          }
          fetch('/api/user/update_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
          })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                showToast('Password updated!', 'success');
              } else {
                showToast(data.error || 'Failed to update password', 'error');
              }
            })
            .catch(() => showToast('Network error', 'error'));
        }
      });
    };
  }
});

function createModal({ title, content, confirmText, cancelText, onConfirm, inputType, inputPlaceholder, inputs }) {
  // Remove any existing modal
  const old = document.getElementById('lumon-modal');
  if (old) old.remove();
  const modal = document.createElement('div');
  modal.id = 'lumon-modal';
  modal.innerHTML = `
    <div class="lumon-modal-backdrop"></div>
    <div class="lumon-modal-box">
      <div class="lumon-modal-title">${title}</div>
      <div class="lumon-modal-content">${content || ''}</div>
      <div class="lumon-modal-actions"></div>
    </div>
  `;
  document.body.appendChild(modal);
  const box = modal.querySelector('.lumon-modal-box');
  const actions = box.querySelector('.lumon-modal-actions');
  let input = null;
  let inputEls = [];
  if (inputs && Array.isArray(inputs)) {
    inputs.forEach((inp, idx) => {
      const inputEl = document.createElement('input');
      inputEl.type = inp.type || 'text';
      inputEl.placeholder = inp.placeholder || '';
      inputEl.className = 'lumon-modal-input';
      actions.appendChild(inputEl);
      inputEls.push(inputEl);
    });
    if (inputEls[0]) setTimeout(() => inputEls[0].focus(), 100);
  } else if (inputType) {
    input = document.createElement('input');
    input.type = inputType;
    input.placeholder = inputPlaceholder || '';
    input.className = 'lumon-modal-input';
    actions.appendChild(input);
    setTimeout(() => input.focus(), 100);
  }
  const confirmBtn = document.createElement('button');
  confirmBtn.className = 'lumon-modal-btn confirm';
  confirmBtn.textContent = confirmText || 'OK';
  actions.appendChild(confirmBtn);
  if (cancelText) {
    const cancelBtn = document.createElement('button');
    cancelBtn.className = 'lumon-modal-btn cancel';
    cancelBtn.textContent = cancelText;
    actions.appendChild(cancelBtn);
    cancelBtn.onclick = () => modal.remove();
  }
  confirmBtn.onclick = () => {
    if (inputs && Array.isArray(inputs)) {
      const values = inputEls.map(el => el.value);
      if (onConfirm) onConfirm(...values);
    } else if (onConfirm) {
      onConfirm(input ? input.value : undefined);
    }
    modal.remove();
  };
  modal.querySelector('.lumon-modal-backdrop').onclick = () => modal.remove();
}


// --- Username Update ---
const usernameBtn = document.querySelector('.setting-btn.placeholder-btn[onclick*="Username"]');
if (usernameBtn) {
  usernameBtn.onclick = function() {
    createModal({
      title: 'Edit Username',
      inputType: 'text',
      inputPlaceholder: 'Enter new username',
      confirmText: 'Save',
      cancelText: 'Cancel',
      onConfirm: (username) => {
        if (!username) return;
        fetch('/api/user/update_username', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              showToast('Username updated!', 'success');
            } else {
              showToast('Failed to update username', 'error');
            }
          })
          .catch(() => showToast('Network error', 'error'));
      }
    });
  };
}

// --- Password Change ---
const passwordBtn = document.querySelector('.setting-btn.placeholder-btn[onclick*="Change Password"]');
if (passwordBtn) {
  passwordBtn.onclick = function() {
    createModal({
      title: 'Change Password',
      inputType: 'password',
      inputPlaceholder: 'Enter new password',
      confirmText: 'Save',
      cancelText: 'Cancel',
      onConfirm: (password) => {
        if (!password) return;
        fetch('/api/user/update_password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ password })
        })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              showToast('Password updated!', 'success');
            } else {
              showToast('Failed to update password', 'error');
            }
          })
          .catch(() => showToast('Network error', 'error'));
      }
    });
  };
}

// --- Terms & Conditions ---
const termsBtn = document.querySelector('.setting-btn.placeholder-btn[onclick*="Terms"]');
if (termsBtn) {
  termsBtn.onclick = function() {
    createModal({
      title: 'Terms & Conditions',
      content: `<div class='lumon-terms-content'>
        <h3>Welcome to Lumon!</h3>
        <p>By using this app, you agree to the following terms:</p>
        <ul>
          <li><b>Privacy:</b> Your personal data is stored securely and never sold to third parties. You may delete your account at any time.</li>
          <li><b>Content:</b> You are responsible for the content you upload or generate. Do not upload illegal, offensive, or copyrighted material without permission.</li>
          <li><b>Usage:</b> You agree not to misuse the app, attempt unauthorized access, or disrupt service for others.</li>
          <li><b>Changes:</b> Lumon reserves the right to update these terms and will notify users of significant changes.</li>
          <li><b>Disclaimer:</b> This app is provided as-is, without warranties. Use at your own risk.</li>
        </ul>
        <p>Contact support for questions or concerns.</p>
      </div>`,
      confirmText: 'Close'
    });
  };
}
// (Help button/functionality removed)

// --- Logout ---
const logoutBtn = document.querySelector('.setting-btn.logout-btn');
if (logoutBtn) {
  logoutBtn.onclick = async function() {
    try {
      const res = await fetch('/api/logout', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('Logged out!', 'success');
        setTimeout(() => window.location.href = '/', 1000);
      } else {
        showToast('Logout failed', 'error');
      }
    } catch {
      showToast('Network error', 'error');
    }
  };
}


function filterCountries() {
  const query = countrySearch.value.toLowerCase();
  const options = countryList.querySelectorAll('.country-option');
  options.forEach(option => {
    option.style.display = option.textContent.toLowerCase().includes(query) ? '' : 'none';
  });
}

function toggleCountryDropdown() {
  countryDropdown.style.display = countryDropdown.style.display === 'block' ? 'none' : 'block';
  if (countryDropdown.style.display === 'block') {
    countrySearch.focus();
  }
}

function selectCountry(country) {
  selectedCountrySpan.textContent = country;
  countryDropdown.style.display = 'none';
  // Save to backend
  fetch('/api/user/update_country', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ country })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        showToast('Country updated!', 'success');
      } else {
        showToast('Failed to update country', 'error');
      }
    })
    .catch(() => showToast('Network error', 'error'));
}

// Close dropdown when clicking outside
window.addEventListener('click', function(e) {
  if (!countryDropdown.contains(e.target) && !countryBtn.contains(e.target)) {
    countryDropdown.style.display = 'none';
  }
});

if (countryBtn && countryDropdown && countryList && countrySearch && selectedCountrySpan) {
  populateCountries();
  countrySearch.addEventListener('keyup', filterCountries);
}
