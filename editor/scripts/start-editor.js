'use strict';

// Align the editor port with panotour/build_tour.py's default API URL.
process.env.PORT ||= '3199';
require('../MT-Panoramic/server/index.js');
