var App = App || {};
App.models = {};

var animate = function(marker,counter,max) {
	setTimeout(function() {
		if( counter === max ) {
			//marker.setMap(null);
			marker.setRadius(20);
		} else {
			marker.setRadius(marker.getRadius()*1.05);
		}
	}, counter * 75);
};

App.controllers = {

	channel : {
        onOpened : function() {
		    App.utils.sendMessage('opened');
        },
		onMessage : function(message) {
			var api_request = JSON.parse(message.data);
			if( api_request.function === 'reload' ) {
				console.log('page refresh from server');
				App.utils.pageRefresh();
			} else {
				console.log('new event...');
			    App.utils.addMarker(api_request.lat,api_request.lng);
			}
		},
		onError : function() {
			console.log('channel error!?');
		},
		onClose : function() {
			console.log('channel closed.');
		}
	}

};


App.utils = {

	pageRefresh : function() {
		document.location.reload(true);
	},

	sendMessage : function(path, opt_param) {
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/map/channel', true);
		xhr.send();
	},

	initialize : function() {
		var mapStyles = [
		  {
		    "featureType": "water",
		    "stylers": [
		      { "weight": 0.1 },
		      { "color": "#808091" }
		    ]
		  },{
		    "featureType": "administrative.locality",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "poi.business",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "poi.medical",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "poi.park",
		    "stylers": [
		      { "visibility": "simplified" },
		      { "color": "#7d9d76" },
		      { "lightness": 39 }
		    ]
		  },{
		    "featureType": "poi.place_of_worship",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "poi.school",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "poi.sports_complex",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "road.highway",
		    "stylers": [
		      { "visibility": "simplified" },
		      { "color": "#393a80" },
		      { "lightness": -9 },
		      { "weight": 2 }
		    ]
		  },{
		    "featureType": "road.highway",
		    "elementType": "labels.icon",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  },{
		    "featureType": "road.arterial",
		    "stylers": [
		      { "visibility": "simplified" },
		      { "color": "#808080" }
		    ]
		  },{
		    "featureType": "road.arterial",
		    "elementType": "labels",
		    "stylers": [
		      { "visibility": "off" }
		    ]
		  }
		]
		var mapOptions = {
		  center: new google.maps.LatLng(43.0731, -89.4011),
		  zoom: 13,
		  mapTypeId: google.maps.MapTypeId.ROADMAP,
		  styles: mapStyles
		};
		App.map = new google.maps.Map(document.getElementById("map-canvas"),
		    mapOptions);

	},

	initChannel : function(token) {
	    App.models.channel = new goog.appengine.Channel(token);
	    App.models.socket = App.models.channel.open();
	    App.models.socket.onopen = App.controllers.channel.onOpened;
	    App.models.socket.onmessage = App.controllers.channel.onMessage;
	    App.models.socket.onerror = App.controllers.channel.onError;
	    App.models.socket.onclose = App.controllers.channel.onClose;
	},

	addMarker : function(lat,lng) {
		var myLatlng = new google.maps.LatLng(lat,lng);
		var marker = new google.maps.Circle({
		  center: myLatlng,
          radius: 20,
          fillColor: '#AA2222',
          strokeColor: '#AA2222',
          fillOpacity: .2,
		  map: App.map,
		});
		var animation_count = 70;
		for( var i=0; i < animation_count; i++ ) {
			animate(marker,i,animation_count-1);
		}
	}
};

