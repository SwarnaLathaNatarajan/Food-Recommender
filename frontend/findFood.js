const findFood = async () => {
	var myForm = document.getElementById('formID');
	user=myForm.name.value;
	const response = await fetch('http://34.120.175.58/find', {
    method: 'POST',
	mode: 'no-cors',
    body: JSON.stringify({
        'user': myForm.name.value,
		'radius': myForm.radius.value,
		'lat': myForm.latitude.value,
		'lon': myForm.longitude.value,
    }), 
    headers: {
      'Content-Type': 'application/json'
    }
  });
  const myJson = await response.json(); //extract JSON from the http response
  // do something with myJson
}

function redirect(){
    window.open('index.html');
}