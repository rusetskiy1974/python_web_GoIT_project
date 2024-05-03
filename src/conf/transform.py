TRANSFORM_METHOD = {'angle': {
    'format': 'jpg',
    'angle': 45,
    'background': 'blue',
    'width': 300,
    'height': 300,
    'crop': 'scale'
},
    'sepia': {
        'format': 'jpg',
        'group': 'fill',
        'width': 300,
        'height': 300,
        'radius': 20,
        'effect': 'sepia'
    },
    'radius': {
        'format': 'jpg',
        'width': 300,
        'height': 300,
        'crop': 'fill',
        'gravity': 'face',
        'radius': 'max',
        'fetch_format': 'auto'
    }, 'grayscale': {
        'format': 'jpg',
        'effect': 'grayscale',
        'width': 300,
        'height': 300,
        'crop': 'fill',
        'gravity': 'center',
        'border': '5px_solid_red'
    },
    'pixelate': {
        'format': 'jpg',
        'width': 300,
        'height': 200,
        'crop': 'fill',
        'gravity': 'face',
        'effect': 'pixelate:5',
        'fetch_format': 'auto'
    },
    'blur': {
        'format': 'jpg',
        "width": 300,
        "height": 300,
        "crop": "fill",
        "effect": "blur:500",
        "fetch_format": "auto"
    }}
