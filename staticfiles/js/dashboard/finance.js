

(function($) {
    /* "use strict" */
	
 var dlabChartlist = function(){
	
	var screenWidth = $(window).width();
	let draw = Chart.controllers.line.__super__.draw; //draw shadow
		
	var widgetChart4 = function(){
		if(jQuery('#widgetChart4').length > 0 ){
			const widgetChart4 = document.getElementById("widgetChart4").getContext('2d');
			//generate gradient
			const widgetChart4gradientStroke = widgetChart4.createLinearGradient(0, 1, 0, 500);
			widgetChart4gradientStroke.addColorStop(0, "rgba(58, 135, 192, 1)");
			widgetChart4gradientStroke.addColorStop(1, "rgba(58, 135, 192, 1)");

			new Chart(widgetChart4, {
				type: "line",
				data: {
					labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April"],

					datasets: [{
						label: "Sales Stats",
						borderColor: 'transparent',
						pointBackgroundColor: '#3A87C0',
						pointBorderColor: '#3A87C0',
						borderWidth:4,
						borderRadius:10,
						pointHoverBackgroundColor: '#3A87C0',
						pointHoverBorderColor: '#3A87C0',
						backgroundColor: widgetChart4gradientStroke,
						
						data: [12, 20, 16, 13, 16, 24, 20, 21, 19, 23, 17, 15, 20, 21, 18, 10, 24, 29, 21, 11, 14, 19, 21, 17]
					}]
				},
				options: {
					title: {
						display: !1
					},
					tooltips: {
						intersect: !1,
						mode: "nearest",
						xPadding: 10,
						yPadding: 10,
						caretPadding: 10
					},
					
					legend: {
						display: !1
					},
					responsive: !0,
					maintainAspectRatio: !1,
					hover: {
						mode: "index"
					},
					scales: {
						xAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Month"
							}
						}],
						yAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Value"
							},
							ticks: {
								beginAtZero: !0
							}
						}]
					},
					elements: {
						point: {
							radius: 0,
							borderWidth: 0
						}
					},
					layout: {
						padding: {
							left: 0,
							right: 0,
							top: 5,
							bottom: 0
						}
					}
				}
			});

		}
	}
	var widgetChart5 = function(){
		if(jQuery('#widgetChart5').length > 0 ){
			const widgetChart5 = document.getElementById("widgetChart5").getContext('2d');
			//generate gradient
			const widgetChart4gradientStroke = widgetChart5.createLinearGradient(0, 1, 0, 500);
			widgetChart4gradientStroke.addColorStop(0, "rgba(114, 62, 180, 1)");
			widgetChart4gradientStroke.addColorStop(1, "rgba(114, 62, 180, 1)");

			new Chart(widgetChart5, {
				type: "line",
				data: {
					labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April"],

					datasets: [{
						label: "Sales Stats",
						borderColor: 'transparent',
						pointBackgroundColor: '#723EB4',
						pointBorderColor: '#723EB4',
						borderWidth:4,
						borderRadius:10,
						pointHoverBackgroundColor: '#723EB4',
						pointHoverBorderColor: '#723EB4',
						backgroundColor: widgetChart4gradientStroke,
						
						data: [12, 20, 16, 13, 16, 24, 20, 21, 19, 23, 17, 14, 24, 21, 13, 15, 27, 29, 21, 11, 14, 19, 21, 17]
					}]
				},
				options: {
					title: {
						display: !1
					},
					tooltips: {
						intersect: !1,
						mode: "nearest",
						xPadding: 10,
						yPadding: 10,
						caretPadding: 10
					},
					
					legend: {
						display: !1
					},
					responsive: !0,
					maintainAspectRatio: !1,
					hover: {
						mode: "index"
					},
					scales: {
						xAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Month"
							}
						}],
						yAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Value"
							},
							ticks: {
								beginAtZero: !0
							}
						}]
					},
					elements: {
						point: {
							radius: 0,
							borderWidth: 0
						}
					},
					layout: {
						padding: {
							left: 0,
							right: 0,
							top: 5,
							bottom: 0
						}
					}
				}
			});

		}
	}
	var widgetChart6 = function(){
		if(jQuery('#widgetChart6').length > 0 ){
			const widgetChart6 = document.getElementById("widgetChart6").getContext('2d');
			//generate gradient
			const widgetChart4gradientStroke = widgetChart6.createLinearGradient(0, 1, 0, 500);
			widgetChart4gradientStroke.addColorStop(0, "rgba(253, 83, 83, 1)");
			widgetChart4gradientStroke.addColorStop(1, "rgba(253, 83, 83, 1)");

			new Chart(widgetChart6, {
				type: "line",
				data: {
					labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April"],

					datasets: [{
						label: "Sales Stats",
						borderColor: 'transparent',
						pointBackgroundColor: '#FD5353',
						pointBorderColor: '#FD5353',
						borderWidth:4,
						borderRadius:10,
						pointHoverBackgroundColor: '#FD5353',
						pointHoverBorderColor: '#FD5353',
						backgroundColor: widgetChart4gradientStroke,
						
						data: [12, 20, 16, 13, 16, 24, 20, 21, 19, 23, 17, 14, 24, 21, 13, 15, 27, 29, 21, 11, 14, 19, 21, 17]
					}]
				},
				options: {
					title: {
						display: !1
					},
					tooltips: {
						intersect: !1,
						mode: "nearest",
						xPadding: 10,
						yPadding: 10,
						caretPadding: 10
					},
					
					legend: {
						display: !1
					},
					responsive: !0,
					maintainAspectRatio: !1,
					hover: {
						mode: "index"
					},
					scales: {
						xAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Month"
							}
						}],
						yAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Value"
							},
							ticks: {
								beginAtZero: !0
							}
						}]
					},
					elements: {
						point: {
							radius: 0,
							borderWidth: 0
						}
					},
					layout: {
						padding: {
							left: 0,
							right: 0,
							top: 5,
							bottom: 0
						}
					}
				}
			});

		}
	}
	var widgetChart7 = function(){
		if(jQuery('#widgetChart7').length > 0 ){
			const widgetChart7 = document.getElementById("widgetChart7").getContext('2d');
			//generate gradient
			const widgetChart4gradientStroke = widgetChart7.createLinearGradient(0, 1, 0, 500);
			widgetChart4gradientStroke.addColorStop(0, "rgba(72, 193, 157, 1)");
			widgetChart4gradientStroke.addColorStop(1, "rgba(72, 193, 157, 1)");

			new Chart(widgetChart7, {
				type: "line",
				data: {
					labels: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "January", "February", "March", "April"],

					datasets: [{
						label: "Sales Stats",
						borderColor: 'transparent',
						pointBackgroundColor: '#2AC19D',
						pointBorderColor: '#2AC19D',
						borderWidth:4,
						borderRadius:10,
						pointHoverBackgroundColor: '#2AC19D',
						pointHoverBorderColor: '#2AC19D',
						backgroundColor: widgetChart4gradientStroke,
						
						data: [12, 20, 16, 13, 16, 24, 20, 21, 19, 23, 17, 14, 24, 21, 13, 15, 27, 29, 21, 11, 14, 19, 21, 17]
					}]
				},
				options: {
					title: {
						display: !1
					},
					tooltips: {
						intersect: !1,
						mode: "nearest",
						xPadding: 10,
						yPadding: 10,
						caretPadding: 10
					},
					
					legend: {
						display: !1
					},
					responsive: !0,
					maintainAspectRatio: !1,
					hover: {
						mode: "index"
					},
					scales: {
						xAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Month"
							}
						}],
						yAxes: [{
							display: !1,
							gridLines: !1,
							scaleLabel: {
								display: !0,
								labelString: "Value"
							},
							ticks: {
								beginAtZero: !0
							}
						}]
					},
					elements: {
						point: {
							radius: 0,
							borderWidth: 0
						}
					},
					layout: {
						padding: {
							left: 0,
							right: 0,
							top: 5,
							bottom: 0
						}
					}
				}
			});

		}
	}
	var areaChart = function(){
		
		 var options = {
			  series: [{
			  name: 'Income',
			 data: [20,40, 20, 50, 40, 30, 10, 60, 20, 80, 10, 20, 10, 20],
			}, {
			  name: 'Expense',
			  data: [60,20, 60, 20, 60, 20, 50, 40, 52, 35, 50, 35, 20, 10],
			}],
			  chart: {
			  height: 350,
			  type: 'area',
			  toolbar: {
					show: false,
				},
			},
			colors:['#09BD3C', '#FFAA2A'],
			dataLabels: {
			  enabled: false
			},
			fill:{
				type:'solid',
				opacity:1
			},
			stroke: {
			  curve: 'smooth'
			},
			xaxis: {
				categories: ["Week 01", "Week 02", "Week 03", "Week 04", "Week 05", "Week 06", "Week 07", "Week 08", "Week 09", "Week 10", "Week 11", "Week 12", "Week 13", "Week 14", "Week 15", "Week 16"],
				labels: {
					show: true,
					style:{
						colors: '#b9bbbd',
					},
				},
			},
			yaxis: {
				labels: {
					show: true,
					style:{
						colors: '#b9bbbd',
					},
				},
			},
			grid:{
				show: true,
				borderColor: '#E2E2E2',
				yaxis: {
					lines: {
						show: false
					}
				}, 
				xaxis: {
					lines: {
						show: true
					}
				},
			},
			legend:{
				position: 'top',
				fontSize: '14px',
				fontWeight: 700,
				horizontalAlign: 'right',
			},
			tooltip: {
			  x: {
				format: 'dd/MM/yy HH:mm'
			  },
			},
			};

			var chart = new ApexCharts(document.querySelector("#areaChart"), options);
			chart.render();
			
	}
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
 
	/* Function ============ */
		return {
			init:function(){
			},
			
			
			load:function(){
				widgetChart4();
				widgetChart5();
				widgetChart6();
				widgetChart7();
				areaChart();
				
			},
			
			resize:function(){
			}
		}
	
	}();

	
		
	jQuery(window).on('load',function(){
		setTimeout(function(){
			dlabChartlist.load();
		}, 1000); 
		
	});

     

})(jQuery);