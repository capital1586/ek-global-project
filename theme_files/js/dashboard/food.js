

(function($) {
    /* "use strict" */
	
 var dlabChartlist = function(){
	
	var screenWidth = $(window).width();
	let draw = Chart.controllers.line.__super__.draw; //draw shadow
		var donutChart = function(){
		$("span.donut").peity("donut", {
			width: "80",
			height: "80"
		});
	}
	var peityLine = function(){
		$(".peity-line").peity("line", {
			fill: ["rgba(30, 251, 242, 0)"], 
			stroke: 'var(--primary)', 
			strokeWidth: '4', 
			width: "100",
			curve: 'smooth',
			height: "32"
		});
	}
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
 
	/* Function ============ */
		return {
			init:function(){
			},
			
			
			load:function(){
				donutChart();
				peityLine();
				
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