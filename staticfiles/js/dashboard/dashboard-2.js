

(function($) {
    /* "use strict" */
	
 var dlabChartlist = function(){
	
	var screenWidth = $(window).width();
	let draw = Chart.controllers.line.__super__.draw; //draw shadow
	
	
	
	
	
	var activeUser = function(){
		if(jQuery('#activeUserchart').length > 0 ){
			var eChart_2 = echarts.init(document.getElementById('activeUserchart'));
			var option1 = {
				  series: [{
					type: 'liquidFill',
					data: [0.6, 0.5, 0.4],
					radius: '80%',
					color: ['#f33923','#e58b25','#ac235c'],
					backgroundStyle: {
						borderWidth: 0,
						color: 'rgba(255,255,255,0)',
						shadowBlur: 0
					},
					itemStyle: {
						normal: {
							shadowBlur: 5,
							shadowColor: 'rgba(0, 0, 0, .5)'
						}
					},
					outline: {
						borderDistance: 3,
						itemStyle: {
							borderWidth: 5,
							borderColor: '#ac235c',
							shadowBlur: 0,
						}
					},
					label: {
						normal: {
							fontSize: 20
						}
					}
				}]
			};
			eChart_2.setOption(option1);
			eChart_2.resize();	
			/* setInterval(function() {
				chart.config.data.datasets[0].data.push(
					Math.floor(10 + Math.random() * 80)
				);
				chart.config.data.datasets[0].data.shift();
				chart.update();
			}, 2000); */	
			
		}
	}
	
	
	
	
	/* Function ============ */
		return {
			init:function(){
			},
			
			
			load:function(){
				
				activeUser();
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