import axios from 'axios';

export const postDream = async (dream: string, numImages: number, imageSize: 256 | 512, url: string) => {
  return axios
    .post(url + '/api/predict/', { data: [dream, numImages, imageSize] })
    .then(({ data }) => data)
    .catch(e => {
      throw new Error(e && e.message);
    });
};
