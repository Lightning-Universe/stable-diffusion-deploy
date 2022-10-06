import { Box, Link, Stack } from '@mui/material';
import { Links } from './Links';
import { Typography } from './Typography';

export const BuildYourAppBanner = () => {
  return (
    <Link href={Links.tutorial} target={'_blank'}>
      <Stack
        direction={'row'}
        justifyContent={'center'}
        alignItems={'center'}
        sx={theme => ({ background: theme.palette.primary.main, textAlign: 'center' })}
        padding={1}>
        <Typography color={'#FFFFFF'} fontSize={'16px'} fontWeight={400}>
          ⚡️ Learn how to build apps like this!&nbsp;
          <Box component={'span'} fontSize={'16px'} fontWeight={600} fontFamily={'UCity'} lineHeight={'unset'}>
            Get started
          </Box>
        </Typography>
      </Stack>
    </Link>
  );
};
