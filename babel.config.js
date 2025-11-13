module.exports = function (api) {
  api.cache(true);
  return {
    presets: [
      'module:metro-react-native-babel-preset', // 👈 built for RN; includes env, react, and typescript
    ],
    plugins: [
      'react-native-reanimated/plugin', // 👈 must be last if you use Reanimated
    ],
  };
};
