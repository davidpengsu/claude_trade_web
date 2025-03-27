// 페이지네이션 관련 변수들
let currentPage = 1;
const positionsPerPage = 5;
let allClosedPositions = [];

document.addEventListener('DOMContentLoaded', function() {
    // Load all trades initially
    loadTrades('all');
    
    // Symbol filter buttons
    const symbolButtons = document.querySelectorAll('.symbol-btn');
    symbolButtons.forEach(button => {
        button.addEventListener('click', function() {
            symbolButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            loadTrades(this.dataset.symbol);
        });
    });
    
    // 페이지네이션 초기 이벤트 설정
    setupInitialPaginationEvents();
});

// 초기 페이지네이션 이벤트 설정
function setupInitialPaginationEvents() {
    document.querySelectorAll('.page-link[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const pageNum = parseInt(this.dataset.page);
            goToPage(pageNum);
        });
    });
    
    const prevPageLink = document.getElementById('prevPage');
    if (prevPageLink) {
        prevPageLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });
    }
    
    const nextPageLink = document.getElementById('nextPage');
    if (nextPageLink) {
        nextPageLink.addEventListener('click', function(e) {
            e.preventDefault();
            const totalPages = Math.ceil(allClosedPositions.length / positionsPerPage);
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        });
    }
}

function loadTrades(symbol) {
    const endpoint = symbol === 'all' ? '/api/trades' : `/api/trades/${symbol}`;
    
    document.getElementById('openPositionsContainer').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin mb-3" style="font-size: 2rem;"></i>
            포지션 로딩 중...
        </div>
    `;
    document.getElementById('closedPositionsContainer').innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin mb-3" style="font-size: 2rem;"></i>
            포지션 로딩 중...
        </div>
    `;
    
    // 페이지네이션 숨기기
    if (document.getElementById('paginationContainer')) {
        document.getElementById('paginationContainer').style.display = 'none';
    }
    
    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            displayOpenPositions(data.open_positions);
            
            // 클로즈 포지션 저장 및 페이지네이션 설정
            allClosedPositions = data.closed_positions;
            setupPagination(allClosedPositions);
            displayClosedPositions(getCurrentPagePositions());
        })
        .catch(error => {
            console.error('Error fetching trades:', error);
            document.getElementById('openPositionsContainer').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle mb-3" style="font-size: 2.5rem; color: var(--text-secondary);"></i>
                    데이터 로딩 오류
                </div>
            `;
            document.getElementById('closedPositionsContainer').innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-circle mb-3" style="font-size: 2.5rem; color: var(--text-secondary);"></i>
                    데이터 로딩 오류
                </div>
            `;
        });
}

// 현재 페이지의 포지션 데이터 가져오기
function getCurrentPagePositions() {
    const startIndex = (currentPage - 1) * positionsPerPage;
    const endIndex = startIndex + positionsPerPage;
    return allClosedPositions.slice(startIndex, endIndex);
}

// 페이지네이션 설정
function setupPagination(positions) {
    const paginationContainer = document.getElementById('paginationContainer');
    if (!paginationContainer) return;
    
    const totalPages = Math.ceil(positions.length / positionsPerPage);
    
    // 페이지가 1개 이하면 페이지네이션 숨기기
    if (totalPages <= 1) {
        paginationContainer.style.display = 'none';
        return;
    }
    
    // 페이지네이션 UI 표시
    const paginationElement = paginationContainer.querySelector('.pagination');
    if (!paginationElement) return;
    
    let paginationHTML = `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="javascript:void(0);" id="prevPage" aria-label="이전">
                <i class="fas fa-chevron-left"></i>
            </a>
        </li>
    `;
    
    // 페이지 번호 버튼 생성
    for (let i = 1; i <= totalPages; i++) {
        paginationHTML += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="javascript:void(0);" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    paginationHTML += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="javascript:void(0);" id="nextPage" aria-label="다음">
                <i class="fas fa-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationElement.innerHTML = paginationHTML;
    paginationContainer.style.display = 'flex';
    
    // 이벤트 리스너 다시 등록
    document.querySelectorAll('.page-link[data-page]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            if (this.dataset.page) {
                const pageNum = parseInt(this.dataset.page);
                goToPage(pageNum);
            }
        });
    });
    
    const prevPageBtn = document.getElementById('prevPage');
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        });
    }
    
    const nextPageBtn = document.getElementById('nextPage');
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        });
    }
}

// 페이지 이동 함수
function goToPage(pageNum) {
    currentPage = pageNum;
    displayClosedPositions(getCurrentPagePositions());
    setupPagination(allClosedPositions);
}

function displayOpenPositions(positions) {
    const container = document.getElementById('openPositionsContainer');
    
    if (positions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exchange-alt mb-3" style="font-size: 2.5rem; color: var(--text-secondary);"></i>
                오픈 포지션이 없습니다
            </div>
        `;
        return;
    }
    
    let html = '';
    positions.forEach(position => {
        const positionType = position.positionType === 'long' ? 'position-long' : 'position-short';
        const positionIcon = position.positionType === 'long' ? 'fa-long-arrow-alt-up' : 'fa-long-arrow-alt-down';
        const symbolClass = `symbol-icon-${position.symbol.toLowerCase().substring(0, 3)}`;
        const positionTypeKorean = position.positionType === 'long' ? '롱' : '숏'
        const sideKorean = position.side === 'Buy' ? '포지션' : '포지션';
        // const sideKorean = position.side === 'Buy' ? '매수' : '매도';

        html += `
        <div class="trade-row">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <span class="symbol-icon ${symbolClass}">${position.symbol.substring(0, 1)}</span>
                    <strong>${position.symbol}</strong>
                    <span class="position-badge ${positionType}">
                        <i class="fas ${positionIcon} me-1"></i>
                        ${positionTypeKorean} ${sideKorean}
                    </span>
                </div>
                <div>
                    <span class="badge-time">
                        <i class="far fa-clock me-1"></i>
                        ${formatDate(position.entry_time)}
                    </span>
                </div>
            </div>
            <div class="row g-3 mt-1">
                <div class="col-6 col-md-4">
                    <div class="data-label">진입 가격</div>
                    <div class="data-value">${formatPrice(position.price)} USD</div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="data-label">수량</div>
                    <div class="data-value">${formatQuantity(position.quantity)}</div>
                </div>
                <div class="col-6 col-md-4">
                    <div class="data-label">레버리지</div>
                    <div class="data-value">${position.leverage}x</div>
                </div>
                <div class="col-6 col-md-6">
                    <div class="data-label">익절가</div>
                    <div class="data-value">${position.takeProfit ? formatPrice(position.takeProfit) + ' USD' : '설정 안됨'}</div>
                </div>
                <div class="col-6 col-md-6">
                    <div class="data-label">손절가</div>
                    <div class="data-value">${position.stopLoss ? formatPrice(position.stopLoss) + ' USD' : '설정 안됨'}</div>
                </div>
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayClosedPositions(positions) {
    const container = document.getElementById('closedPositionsContainer');
    const paginationContainer = document.getElementById('paginationContainer');
    
    if (!container) return;
    
    if (allClosedPositions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history mb-3" style="font-size: 2.5rem; color: var(--text-secondary);"></i>
                클로즈된 포지션이 없습니다
            </div>
        `;
        if (paginationContainer) {
            paginationContainer.style.display = 'none';
        }
        return;
    }
    
    if (positions.length === 0) {
        // 현재 페이지에 표시할 항목이 없는 경우 (페이지 이동 문제)
        goToPage(1); // 첫 페이지로 이동
        return;
    }
    
    let html = '';
    positions.forEach(position => {
        const positionType = position.positionType === 'long' ? 'position-long' : 'position-short';
        const positionIcon = position.positionType === 'long' ? 'fa-long-arrow-alt-up' : 'fa-long-arrow-alt-down';
        const pnlClass = position.pnl >= 0 ? 'profit' : 'loss';
        const pnlIcon = position.pnl >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
        const symbolClass = `symbol-icon-${position.symbol.toLowerCase().substring(0, 3)}`;
        const positionTypeKorean = position.positionType === 'long' ? '롱' : '숏';
        const sideKorean = position.side === 'Buy' ? '포지션' : '포지션';
        
        html += `
        <div class="trade-row">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <div>
                    <span class="symbol-icon ${symbolClass}">${position.symbol.substring(0, 1)}</span>
                    <strong>${position.symbol}</strong>
                    <span class="position-badge ${positionType}">
                        <i class="fas ${positionIcon} me-1"></i>
                        ${positionTypeKorean} ${sideKorean}
                    </span>
                </div>
                <div class="${pnlClass}">
                    <i class="fas ${pnlIcon}"></i>
                    ${formatPnl(position.pnl)}
                </div>
            </div>
            <div class="row g-3 mt-1">
                <div class="col-6 col-md-3">
                    <div class="data-label">진입 가격</div>
                    <div class="data-value">${formatPrice(position.entry_price)} USD</div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="data-label">청산 가격</div>
                    <div class="data-value">${formatPrice(position.exit_price)} USD</div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="data-label">수량</div>
                    <div class="data-value">${formatQuantity(position.quantity)}</div>
                </div>
                <div class="col-6 col-md-3">
                    <div class="data-label">레버리지</div>
                    <div class="data-value">${position.leverage}x</div>
                </div>
                <div class="col-6">
                    <div class="data-label">오픈 시간</div>
                    <div class="data-value">
                        <i class="far fa-calendar me-1" style="opacity: 0.6;"></i>
                        ${formatDateTime(position.entry_time)}
                    </div>
                </div>
                <div class="col-6">
                    <div class="data-label">클로즈 시간</div>
                    <div class="data-value">
                        <i class="far fa-calendar-check me-1" style="opacity: 0.6;"></i>
                        ${formatDateTime(position.exit_time)}
                    </div>
                </div>
            </div>
        </div>
        `;
    });
    
    container.innerHTML = html;
}

function formatPrice(price) {
    return parseFloat(price).toFixed(2);
}

function formatQuantity(qty) {
    return parseFloat(qty).toFixed(8);
}

function formatPnl(pnl) {
    const value = parseFloat(pnl);
    return (value >= 0 ? '+' : '') + value.toFixed(8);
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    const options = { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit'
    };
    
    return date.toLocaleDateString('ko-KR', options);
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'N/A';
    
    const date = new Date(dateStr);
    const options = { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    };
    
    return date.toLocaleDateString('ko-KR', options);
}