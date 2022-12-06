const path = require('path');
const fs = require('fs');
const cracoBabelLoader = require('craco-babel-loader');

// manage relative paths to packages
const appDirectory = fs.realpathSync(process.cwd());
const resolvePackage = relativePath => path.resolve(appDirectory, relativePath);

const IS_DEV = process.env.NODE_ENV !== 'production';

const webpack = {
  configure: {
    output: {
      publicPath: './',
    },
  },
};

module.exports = {
  ...(IS_DEV ? {} : { webpack }),
  plugins: [
    {
      plugin: cracoBabelLoader,
      options: {
        includes: [resolvePackage('node_modules/lightning-ui')],
      },
    },
  ],
};
