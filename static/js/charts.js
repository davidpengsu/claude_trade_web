/**
 * Trading Dashboard Charts
 * Contains functions to create and update various charts used in the dashboard
 */

// Theme colors
const chartColors = {
    background: '#1e1e1e',
    gridLines: 'rgba(255, 255, 255, 0.1)',
    textColor: '#a0a0a0',
    titleColor: '#e0e0e0',
    success: '#4caf50',
    danger: '#d32f2f',
    info: '#2196f3',
    warning: '#ff9800',
    successFill: 'rgba(76, 175, 80, 0.1)',
    dangerFill: 'rgba(211, 47, 47, 0.1)',
    infoFill: 'rgba(33, 150, 243, 0.1)',
    warningFill: 'rgba(255, 152, 0, 0.1)'
};

/**
 * Create a line chart for performance data
 * @param {string} canvasId - The ID of the canvas element
 * @param {Array} datasets - Array of dataset objects
 * @param {Array} labels - Array of labels for the x-axis
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created Chart instance
 */
function createPerformanceChart(canvasId, datasets, labels, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const defaultOptions = {
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
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: chartOptions
    });
}

/**
 * Create a bar chart for PnL data
 * @param {string} canvasId - The ID of the canvas element
 * @param {Array} pnlData - Array of PnL values
 * @param {Array} labels - Array of labels for the x-axis
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created Chart instance
 */
function createPnLChart(canvasId, pnlData, labels, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generate background colors based on positive/negative values
    const backgroundColors = pnlData.map(value => {
        return value >= 0 ? chartColors.successFill : chartColors.dangerFill;
    });
    
    // Generate border colors based on positive/negative values
    const borderColors = pnlData.map(value => {
        return value >= 0 ? chartColors.success : chartColors.danger;
    });
    
    const defaultOptions = {
        responsive: true,
        plugins: {
            legend: {
                display: false
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
                    text: 'Profit/Loss',
                    color: chartColors.titleColor
                }
            }
        }
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'PnL',
                data: pnlData,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Create a dual-axis chart for monthly performance (PnL and trade count)
 * @param {string} canvasId - The ID of the canvas element
 * @param {Array} pnlData - Array of PnL values
 * @param {Array} tradeCountData - Array of trade count values
 * @param {Array} labels - Array of labels for the x-axis
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created Chart instance
 */
function createMonthlyChart(canvasId, pnlData, tradeCountData, labels, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Generate background colors based on positive/negative values
    const backgroundColors = pnlData.map(value => {
        return value >= 0 ? 'rgba(76, 175, 80, 0.6)' : 'rgba(211, 47, 47, 0.6)';
    });
    
    // Generate border colors based on positive/negative values
    const borderColors = pnlData.map(value => {
        return value >= 0 ? 'rgba(76, 175, 80, 1)' : 'rgba(211, 47, 47, 1)';
    });
    
    const defaultOptions = {
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
                    text: 'PnL',
                    color: chartColors.titleColor
                }
            },
            y1: {
                position: 'right',
                grid: {
                    drawOnChartArea: false
                },
                ticks: {
                    color: chartColors.textColor
                },
                title: {
                    display: true,
                    text: 'Trade Count',
                    color: chartColors.titleColor
                }
            }
        }
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Monthly PnL',
                    data: pnlData,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 1
                },
                {
                    label: 'Trade Count',
                    data: tradeCountData,
                    type: 'line',
                    yAxisID: 'y1',
                    borderColor: chartColors.info,
                    backgroundColor: chartColors.infoFill,
                    borderWidth: 2,
                    pointRadius: 3,
                    fill: false
                }
            ]
        },
        options: chartOptions
    });
}

/**
 * Create a doughnut chart for win/loss ratio
 * @param {string} canvasId - The ID of the canvas element
 * @param {number} wins - Number of winning trades
 * @param {number} losses - Number of losing trades
 * @param {Object} options - Additional chart options
 * @returns {Chart} The created Chart instance
 */
function createWinLossChart(canvasId, wins, losses, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    color: chartColors.textColor
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.raw || 0;
                        const total = wins + losses;
                        const percentage = Math.round((value / total) * 100);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        },
        cutout: '60%'
    };
    
    const chartOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Wins', 'Losses'],
            datasets: [{
                data: [wins, losses],
                backgroundColor: [chartColors.success, chartColors.danger],
                borderColor: [chartColors.success, chartColors.danger],
                borderWidth: 1
            }]
        },
        options: chartOptions
    });
}

/**
 * Load chart data from API endpoint
 * @param {string} url - API endpoint URL
 * @param {Function} callback - Callback function to handle the data
 */
function loadChartData(url, callback) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
        });
}

/**
 * Format datetime string to local date
 * @param {string} datetimeStr - Datetime string in ISO format
 * @returns {string} Formatted date string
 */
function formatDateTime(datetimeStr) {
    const date = new Date(datetimeStr);
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Format number as currency
 * @param {number} value - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

/**
 * Format number as percentage
 * @param {number} value - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage string
 */
function formatPercentage(value, decimals = 2) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value / 100);
}
