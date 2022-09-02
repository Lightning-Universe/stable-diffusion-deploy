import axios from 'axios';

export const postDream = async (dream: string, numImages: number, imageSize: 256 | 512, url: string) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  const config = {
    headers: headers,
  };

  return axios
    .post(url + '/api/predict/', { dream: dream, num_images: numImages, image_size: imageSize }, config)
    .then(({ data }) => data)
    .catch(e => {
      throw new Error(e && e.message);
    });
};
