import { Link, Stack } from '@mui/material';
import SlackIcon from '../assets/Slack.svg';
import { Links } from './Links';
import { Typography } from './Typography';

export const Footer = ({ apiLink }: { apiLink?: string }) => (
  <Stack direction={{ xs: 'column', md: 'row' }} alignItems={'center'} justifyContent={'center'}>
    <Stack direction={'row'} alignItems={'center'} justifyContent={'center'}>
      <Typography fontSize={'14px'} fontFamily={'Roboto'}>
        <Link href={Links.usage} target={'_blank'}>
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
