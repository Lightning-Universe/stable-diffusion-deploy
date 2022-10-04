import { Box, Link, Stack } from '@mui/material';
import SlackIcon from '../assets/Slack.svg';
import { Typography } from './Typography';

export enum Links {
  stableDiffusion = 'https://stability.ai/blog/stable-diffusion-public-release',
  runYouOwnVersion = 'https://lightning.ai/app/g1VJ8GZ7XF-AI-powered%20HackerNews', // todo: replace this with actual id from spreadsheet.
  slack = 'https://wsvbs-01gbz6hpp0nx2ahp49ect17q2n.litng-ai-03.litng.ai/slack/start',
  twitter = 'https://twitter.com/LightningAI',
  lightningAI = 'https://lightning.ai/',
  license = 'https://huggingface.co/spaces/CompVis/stable-diffusion-license',
  github = 'https://github.com/Lightning-AI/LAI-Stable-Diffusion-App',
}

export const AppDetailsFooter = ({ apiLink }: { apiLink?: string }) => (
  <Stack
    direction={{ xs: 'column', md: 'row' }}
    alignItems={'center'}
    justifyContent={'center'}
    rowGap={{ xs: 2, md: 0 }}>
    <Stack direction={'row'} alignItems={'center'} justifyContent={'center'}>
      <Typography fontSize={'14px'} fontFamily={'Roboto'}>
        <Link href={Links.license} target={'_blank'}>
          Usage
        </Link>
      </Typography>
      <VerticalLine />
      <Typography fontSize={'14px'} fontFamily={'Roboto'}>
        <Link href={apiLink} target={'_blank'}>
          API
        </Link>
      </Typography>
      <VerticalLine />

      <Typography fontSize={'14px'} fontFamily={'Roboto'}>
        <Link
          href={Links.slack}
          target={'_blank'}
          rel="noreferrer"
          underline={'none'}
          display={'flex'}
          flexDirection={'row'}
          justifyContent={'center'}>
          <img src={SlackIcon} alt={'app-dream'} />
          &nbsp; Bot
        </Link>
      </Typography>
      <VerticalLine />
      <Typography fontSize={'14px'} fontFamily={'Roboto'}>
        <Link href={Links.github} target={'_blank'}>
          Get the Code
        </Link>
      </Typography>
    </Stack>
  </Stack>
);

const VerticalLine = () => (
  <Typography color={'#C9CCD1'} fontWeight={200}>
    &nbsp;|&nbsp;
  </Typography>
);

export const BuildYourAppBanner = () => {
  return (
    <Box sx={theme => ({ background: theme.palette.primary.main, textAlign: 'center' })} padding={1}>
      <Typography fontSize={'14px'} fontWeight={600}>
        <Link href={Links.lightningAI} target={'_blank'} color={'#fff'}>
          Learn how to build apps like this!
        </Link>
      </Typography>
    </Box>
  );
};
