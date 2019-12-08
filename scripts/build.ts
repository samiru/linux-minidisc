console.log("XXXXXXXXXXXXXX");

import * as shell from 'shelljs';
//var shell = require('shelljs');

shell.exec('qmake');
shell.exec('make');