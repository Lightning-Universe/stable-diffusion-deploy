// https://stackoverflow.com/questions/7184573/pick-up-the-android-version-in-the-browser-by-javascript
// return a floating point version number like this major.minor
export const getAndroidVersion = (): number => {
  var ua = navigator.userAgent;
  if (ua.indexOf('Android') >= 0) {
    var androidversion = parseFloat(ua.slice(ua.indexOf('Android') + 8));
    return androidversion;
  }
  return 0;
};
