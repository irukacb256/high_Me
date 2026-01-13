document.addEventListener('DOMContentLoaded', () => {
    initDates();
    renderJobs();
});

function initDates() {
    const dateContainer = document.getElementById('date-container');
    const weekChars = ['日', '月', '火', '水', '木', '金', '土'];
    const today = new Date();
    let html = '';
    for(let i = 0; i < 30; i++) {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        const dayLabel = weekChars[d.getDay()];
        const dateNum = d.getDate();
        const displayDay = (i === 0) ? '今日' : dayLabel;
        const activeClass = (i === 0) ? 'active' : '';
        html += `<div class="date-item ${activeClass}" onclick="selectDate(this)">
                    <span class="d-day">${displayDay}</span>
                    <span class="d-num">${dateNum}</span>
                 </div>`;
    }
    dateContainer.innerHTML = html;
}

function selectDate(el) {
    document.querySelectorAll('.date-item').forEach(d => d.classList.remove('active'));
    el.classList.add('active');
}

function renderJobs() {
    const grid = document.getElementById('job-grid');
    if(!grid) return;
    jobsData.forEach((j, index) => {
        const card = document.createElement('div');
        card.className = "job-card";
        card.onclick = () => openDetail(index);
        card.innerHTML = `
            <div class="job-img" style="background-image: url('https://placehold.co/300x200/${j.img}/white?text=Job');">
                <div class="badge-red">🕒 締切間近</div>
                <div class="badge-grey">未経験歓迎</div>
                <div class="fav-icon">♡</div>
            </div>
            <div class="job-body">
                <div class="job-title">${j.t}</div>
                <div class="job-meta">🕒 ${j.time}</div>
                <div class="job-meta">📍 ${j.p}</div>
                <div class="job-price">${j.m}</div>
            </div>
        `;
        grid.appendChild(card);
    });
}