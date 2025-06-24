const portfolioAllocationChartCanvas = document.querySelector("#portfolio-allocation-chart");


function getDoughnutChartData(rawData) {
    if (typeof rawData === "string") {
        chartData = JSON.parse(rawData);
    } else {
        chartData = rawData;
    };
    const allocationData = chartData["data"];
    const colors = chartData["colors"];
    let labels = []
    let data = []

    for (const [stock, allocation] of Object.entries(allocationData)) {
        labels.push(stock);
        data.push(allocation);
    };

    return {
        labels: labels,
        datasets: [{
            label: 'Portfolio Allocation',
            data: data,
            backgroundColor: colors,
            hoverOffset: 4,
            borderWidth: 0.8,
            color: "#f2f2f2",
        }]
    };
};


if (portfolioAllocationChartCanvas) {

    const doughnutChartConfig = {
        type: 'doughnut',
        data: getDoughnutChartData(portfolioAllocationChartCanvas.dataset.chartdata),
        options: {
            responsive: true,
            aspectRatio: 0.55,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    align: 'start',
                    labels: {
                        font: {
                            size: 11,
                            weight: 500,
                        },
                        color: "#f2f2f2",
                        textAlign: 'left',
                        padding: 10,
                        generateLabels: function (chart) {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                const {
                                    labels: {
                                        pointStyle
                                    }
                                } = chart.legend.options;

                                const max = data.datasets[0].data.reduce((a, b) => (a + b), 0);

                                return data.labels.map((label, index) => {
                                    const meta = chart.getDatasetMeta(0);
                                    const style = meta.controller.getStyle(index);
                                    
                                    return {
                                        text: `${label} (${(data.datasets[0].data[index] * 100 / max).toFixed(2)}%)`,
                                        fillStyle: style.backgroundColor,
                                        strokeStyle: style.borderColor,
                                        lineWidth: style.borderWidth,
                                        pointStyle: pointStyle,
                                        hidden: !chart.getDataVisibility(index),

                                        // Extra data used for toggling the correct item
                                        index: index
                                    };
                                });
                            }
                            return [];
                        }
                    },
                    rtl: false,
                },
                tooltip: {
                    callbacks: {
                        afterLabel: function (context) {
                            const total = context.chart.data.datasets[0].data.reduce((acc, val) => acc + val);
                            const currentValue = context.dataset.data[context.dataIndex];
                            const percentage = ((currentValue / total) * 100).toFixed(2);
                            return `Percentage: ${percentage}%`;
                        }
                    },
                }
            }
        }
    };

    const portfolioAllocationChart = new Chart(portfolioAllocationChartCanvas, doughnutChartConfig);

    // Function to update chart with new data
    function updateLineChart(chart, rawData) {
        chart.data.datasets = getLineChartData(rawData).datasets;
        chart.update();
    };
};
