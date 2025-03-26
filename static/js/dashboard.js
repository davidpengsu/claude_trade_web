/**
 * Dashboard.js
 * Contains functionality for the main trading dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializePerformanceChart();
    initializeRefreshButtons();
    setupDataUpdates();
    setupNotifications();
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

/**
 * Initialize the performance chart on the dashboard
 */
function initializePerformanceChart() {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;
    
    const ctx2d = ctx.getContext('2d');
    
    // Generate the last 30 days
    const labels = [];
    const ethData = [];
    const btcData = [];
    const solData = [];
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Simulate cumulative performance
        const ethBase = Math.random() * 10 - 3;  // Random base between -3 and 7
        const btcBase = Math.random() * 12 - 4;  // Random base between -4 and 8
        const solBase = Math.random() * 15 - 6;  // Random base between -6 and 9
        
        if (i === 29) {
            ethData.push(ethBase);
            btcData.push(btcBase);
            solData.push(solBase);
        } else {
            const ethChange = Math.random() * 2 - 0.8;  // Random change between -0.8 and 1.2
            const btcChange = Math.random() * 2.5 - 1;  // Random change between -1 and 1.5
            const solChange = Math.random() * 3 - 1.2;  // Random change between -1.2 and 1.8
            
            ethData.push(ethData[ethData.length - 1] + ethChange);
            btcData.push(btcData[btcData.length - 1] + btcChange);
            solData.push(solData[solData.length - 1] + solChange);
        }
    }
    
    const chartColors = {
        background: '#1e1e1e',
        gridLines: 'rgba(255, 255, 255, 0.1)',
        textColor: '#a0a0a0',
        titleColor: '#e0e0e0',
        eth: '#4caf50',
        btc: '#ff9800',
        sol: '#2196f3',
        ethFill: 'rgba(76, 175, 80, 0.1)',
        btcFill: 'rgba(255, 152, 0, 0.1)',
        solFill: 'rgba(33, 150, 243, 0.1)'
    };
    
    const chart = new Chart(ctx2d, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'ETH',
                    data: ethData,
                    borderColor: chartColors.eth,
                    backgroundColor: chartColors.ethFill,
                    tension: 0.3,
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'BTC',
                    data: btcData,
                    borderColor: chartColors.btc,
                    backgroundColor: chartColors.btcFill,
                    tension: 0.3,
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4
                },
                {
                    label: 'SOL',
                    data: solData,
                    borderColor: chartColors.sol,
                    backgroundColor: chartColors.solFill,
                    tension: 0.3,
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: chartColors.textColor
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: {
                        color: chartColors.gridLines
                    },
                    ticks: {
                        color: chartColors.textColor
                    }
                },
                y: {
                    grid: {
                        color: chartColors.gridLines
                    },
                    ticks: {
                        color: chartColors.textColor
                    },
                    title: {
                        display: true,
                        text: 'Profit/Loss (%)',
                        color: chartColors.titleColor
                    }
                }
            }
        }
    });
    
    // Add event listener for chart period selection
    const periodButtons = document.querySelectorAll('.chart-period');
    if (periodButtons) {
        periodButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const period = this.dataset.period;
                updateChartPeriod(chart, period);
                
                // Update active button
                periodButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
}

/**
 * Update chart data based on selected period
 * @param {Chart} chart - Chart.js instance
 * @param {string} period - Time period ('7d', '30d', '90d', 'all')
 */
function updateChartPeriod(chart, period) {
    // This function would fetch new data from the server based on the period
    // For now, let's simulate with random data
    
    let days = 30;
    switch(period) {
        case '7d':
            days = 7;
            break;
        case '30d':
            days = 30;
            break;
        case '90d':
            days = 90;
            break;
        case 'all':
            days = 180;
            break;
    }
    
    // Generate new labels and data
    const labels = [];
    const ethData = [];
    const btcData = [];
    const solData = [];
    
    for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Generate random data
        ethData.push(Math.random() * 20 - 10);
        btcData.push(Math.random() * 25 - 10);
        solData.push(Math.random() * 30 - 15);
    }
    
    // Update chart data
    chart.data.labels = labels;
    chart.data.datasets[0].data = ethData;
    chart.data.datasets[1].data = btcData;
    chart.data.datasets[2].data = solData;
    chart.update();
}

/**
 * Initialize refresh buttons
 */
function initializeRefreshButtons() {
    const refreshButtons = document.querySelectorAll('.btn-refresh');
    if (refreshButtons) {
        refreshButtons.forEach(button => {
            button.addEventListener('click', function() {
                const target = this.dataset.target;
                refreshData(target);
                
                // Add loading spinner
                const originalHtml = this.innerHTML;
                this.innerHTML = '<div class="loading-spinner"></div>';
                
                // Restore original content after 1 second
                setTimeout(() => {
                    this.innerHTML = originalHtml;
                }, 1000);
            });
        });
    }
}

/**
 * Refresh data for a specific section
 * @param {string} target - Section to refresh
 */
function refreshData(target) {
    // This function would fetch fresh data from the server
    console.log(`Refreshing data for ${target}`);
    
    // For demonstration, let's simulate some data updates
    switch(target) {
        case 'latest-trades':
            refreshLatestTrades();
            break;
        case 'account-balance':
            refreshAccountBalance();
            break;
        case 'performance-chart':
            refreshPerformanceChart();
            break;
        case 'recent-decisions':
            refreshRecentDecisions();
            break;
        default:
            console.log('Unknown refresh target');
    }
}

/**
 * Refresh latest trades data
 */
function refreshLatestTrades() {
    fetch('/api/latest-trades')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Refreshed latest trades data:', data);
            // Update the trades table with new data
            // This would be implemented in a real application
        })
        .catch(error => {
            console.error('Error refreshing trades data:', error);
            showNotification('Error refreshing trades data', 'danger');
        });
}

/**
 * Refresh account balance data
 */
function refreshAccountBalance() {
    fetch('/api/account-balance')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Refreshed account balance data:', data);
            // Update the balance cards with new data
            // This would be implemented in a real application
        })
        .catch(error => {
            console.error('Error refreshing account balance data:', error);
            showNotification('Error refreshing account balance', 'danger');
        });
}

/**
 * Refresh performance chart data
 */
function refreshPerformanceChart() {
    fetch('/api/performance-data')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Refreshed performance data:', data);
            // Update the performance chart with new data
            // This would be implemented in a real application
        })
        .catch(error => {
            console.error('Error refreshing performance data:', error);
            showNotification('Error refreshing performance chart', 'danger');
        });
}

/**
 * Refresh recent decisions data
 */
function refreshRecentDecisions() {
    fetch('/api/recent-decisions')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Refreshed recent decisions data:', data);
            // Update the decisions list with new data
            // This would be implemented in a real application
        })
        .catch(error => {
            console.error('Error refreshing decisions data:', error);
            showNotification('Error refreshing recent decisions', 'danger');
        });
}

/**
 * Setup automatic data updates
 */
function setupDataUpdates() {
    // Refresh data every 60 seconds
    setInterval(() => {
        refreshLatestTrades();
        refreshAccountBalance();
        refreshRecentDecisions();
    }, 60000);
}

/**
 * Setup notification system
 */
function setupNotifications() {
    // Create a container for notifications if it doesn't exist
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
}

/**
 * Show a notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, info, warning, danger)
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notification-container');
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Remove after duration
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}

/**
 * Format currency value
 * @param {number} value - Value to format
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, decimals = 2) {
    if (value === null || value === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

/**
 * Format percentage value
 * @param {number} value - Value to format
 * @param {number} decimals - Decimal places (default: 2)
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, decimals = 2) {
    if (value === null || value === undefined) return '0.00%';
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}

/**
 * Format date
 * @param {string} dateStr - Date string
 * @param {boolean} includeTime - Whether to include time (default: true)
 * @returns {string} Formatted date string
 */
function formatDate(dateStr, includeTime = true) {
    if (!dateStr) return '-';
    
    const date = new Date(dateStr);
    if (includeTime) {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } else {
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }
}

/**
 * Handle click on a trade row to show details
 */
function setupTradeRowClicks() {
    const tradeRows = document.querySelectorAll('tr.trade-row');
    if (tradeRows) {
        tradeRows.forEach(row => {
            row.addEventListener('click', function() {
                const tradeId = this.dataset.tradeId;
                if (tradeId) {
                    showTradeDetails(tradeId);
                }
            });
        });
    }
}

/**
 * Show trade details in a modal
 * @param {string} tradeId - Trade ID
 */
function showTradeDetails(tradeId) {
    fetch(`/api/trade/${tradeId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Create modal content with trade details
            const modalTitle = `Trade Details: ${data.symbol}`;
            let modalBody = `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Trade ID:</strong> ${data.tradeId}</p>
                        <p><strong>Symbol:</strong> ${data.symbol}</p>
                        <p><strong>Position Type:</strong> <span class="badge ${data.positionType === 'long' ? 'position-long' : 'position-short'}">${data.positionType}</span></p>
                        <p><strong>Order Type:</strong> ${data.orderType}</p>
                        <p><strong>Side:</strong> ${data.side}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Quantity:</strong> ${data.quantity}</p>
                        <p><strong>Price:</strong> ${formatCurrency(data.price)}</p>
                        <p><strong>Leverage:</strong> ${data.leverage}x</p>
                        <p><strong>PnL:</strong> <span class="${data.pnl > 0 ? 'text-success' : 'text-danger'}">${data.pnl ? formatCurrency(data.pnl) : '-'}</span></p>
                        <p><strong>Status:</strong> <span class="badge bg-info">${data.orderStatus}</span></p>
                    </div>
                </div>
                <hr>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Take Profit:</strong> ${data.takeProfit ? formatCurrency(data.takeProfit) : 'Not set'}</p>
                        <p><strong>Stop Loss:</strong> ${data.stopLoss ? formatCurrency(data.stopLoss) : 'Not set'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Execution Time:</strong> ${formatDate(data.executionTime)}</p>
                        <p><strong>Created At:</strong> ${formatDate(data.createdAt)}</p>
                    </div>
                </div>
            `;
            
            // Show modal with trade details
            const modal = new bootstrap.Modal(document.getElementById('tradeDetailsModal'));
            document.getElementById('tradeDetailsModalLabel').textContent = modalTitle;
            document.getElementById('tradeDetailsModalBody').innerHTML = modalBody;
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching trade details:', error);
            showNotification('Error fetching trade details', 'danger');
        });
}

/**
 * Toggle visibility of additional details
 * @param {string} elementId - Element ID to toggle
 */
function toggleDetails(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.style.display === 'none' || element.style.display === '') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
}
