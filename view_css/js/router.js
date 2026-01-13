function goToScreen(screenId) {
    document.querySelectorAll('.screen').forEach(el => el.classList.remove('active'));
    const target = document.getElementById(screenId);
    if(target) target.classList.add('active');
    if(screenId === 'map-screen' && window.mapInstance) {
        setTimeout(() => {
            google.maps.event.trigger(window.mapInstance, 'resize');
            if(window.mapCenterData) window.mapInstance.setCenter(window.mapCenterData);
        }, 100);
    }
}

function switchTab(screenId) {
    goToScreen(screenId);
    const navIds = {
        'home-screen': 'nav-home',
        'fav-screen': 'nav-fav',
        'work-screen': 'nav-work',
        'message-screen': 'nav-msg',
        'mypage-screen': 'nav-mypage'
    };
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    const activeNavId = navIds[screenId];
    if(activeNavId) {
        document.querySelectorAll(`#${activeNavId}`).forEach(t => t.classList.add('active'));
    }
}

function applyPref() {
    const checks = document.querySelectorAll('input[name="pref"]:checked');
    if(checks.length > 0) {
        const val = checks[checks.length-1].value;
        const homeText = document.getElementById('home-location-text');
        const settingText = document.getElementById('setting-pref');
        if(homeText) homeText.innerText = val;
        if(settingText) settingText.innerText = val;
    }
    goToScreen('location-screen');
}

function openSort() {
    const overlay = document.getElementById('overlay');
    const sheet = document.getElementById('sort-sheet');
    if(overlay && sheet) { overlay.classList.add('active'); sheet.classList.add('active'); }
}
function closeSort() {
    const overlay = document.getElementById('overlay');
    const sheet = document.getElementById('sort-sheet');
    if(overlay) overlay.classList.remove('active');
    if(sheet) sheet.classList.remove('active');
}
function selectSort(text) {
    const label = document.getElementById('current-sort-label');
    if(label) label.innerText = text;
    document.querySelectorAll('.sheet-option').forEach(opt => {
        opt.classList.remove('selected');
        if(opt.innerText.trim() === text) opt.classList.add('selected');
    });
    closeSort();
}

function openDetail(index) {
    if(typeof jobsData === 'undefined' || !jobsData[index]) return;
    const job = jobsData[index];
    const setText = (id, txt) => { const el = document.getElementById(id); if(el) el.innerText = txt; };
    setText('d-title', job.t);
    setText('d-price', job.m);
    setText('d-datetime', job.fullTime || job.time);
    const imgEl = document.getElementById('d-img');
    if(imgEl) imgEl.style.backgroundImage = `url('https://placehold.co/600x400/${job.img}/white?text=Job')`;
    
    const otherSec = document.getElementById('other-dates-section');
    const otherList = document.getElementById('other-dates-list');
    if(otherSec && otherList) {
        if(job.hasOtherDates) {
            otherSec.style.display = 'block';
            otherList.innerHTML = `
                <div class="other-date-item">
                    <div class="od-left"><div class="od-date">12/2</div><div class="od-week">火</div></div>
                    <div class="od-center"><div class="od-time">22:00 〜 1:00</div><div class="od-price">¥4,279</div></div>
                    <div class="od-right"><span class="od-status">👤 0 / 1</span></div>
                </div>
                <div class="other-date-item">
                    <div class="od-left"><div class="od-date">12/3</div><div class="od-week">水</div></div>
                    <div class="od-center"><div class="od-time">21:00 〜 1:00</div><div class="od-price">${job.m}</div></div>
                    <div class="od-right"><span class="od-status">👤 0 / 1</span></div>
                </div>
            `;
        } else { otherSec.style.display = 'none'; }
    }
    setText('d-desc', job.desc || "詳細情報なし");
    setText('d-notes', job.notes || "特になし");
    setText('d-address', job.address || "住所情報なし");
    setText('d-shopname', job.shopName || "店舗名なし");
    
    const createList = (items) => (items || []).map(i => `<li>${i}</li>`).join('');
    const itemsEl = document.getElementById('d-items');
    if(itemsEl) itemsEl.innerHTML = createList(job.items);
    const condEl = document.getElementById('d-conditions');
    if(condEl) condEl.innerHTML = createList(job.conditions);

    const reviewEl = document.getElementById('review-list');
    if(reviewEl) {
        if(job.reviews && job.reviews.length > 0) {
            reviewEl.innerHTML = job.reviews.map(r => `
                <div class="review-item">
                    <div class="ri-header"><span class="ri-user">${r.user}</span><span class="ri-date">${r.date}</span></div>
                    <div class="ri-body">${r.text}</div>
                </div>
            `).join('');
        } else { reviewEl.innerHTML = '<p style="color:#999; font-size:0.9rem;">まだレビューはありません。</p>'; }
    }
    const similarEl = document.getElementById('similar-jobs-list');
    if(similarEl) {
        similarEl.innerHTML = jobsData.filter((_, i) => i !== index).slice(0, 3).map(j => `
            <div class="similar-job-card" onclick="openDetail(${jobsData.indexOf(j)})">
                <div class="sjc-img" style="background-image: url('https://placehold.co/300x200/${j.img}/white?text=Job');">
                    <div class="sjc-badge">締切</div>
                </div>
                <div class="sjc-body">
                    <div class="sjc-title">${j.t}</div>
                    <div class="sjc-meta">${j.fullTime || j.time}</div>
                    <div class="sjc-meta">${j.p}</div>
                    <div class="sjc-price">${j.m}</div>
                </div>
            </div>
        `).join('');
    }
    goToScreen('detail-screen');
}