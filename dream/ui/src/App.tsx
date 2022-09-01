import { Notes, Share } from '@mui/icons-material';
import {
  Box,
  CircularProgress,
  Container,
  CssBaseline,
  Fab,
  Grid,
  Link,
  Tooltip,
  Typography as MuiTypography,
  TypographyProps,
} from '@mui/material';
import { useTheme } from '@mui/system';
import { useClipboard } from 'hooks/useClipboard';
import { useLightningState } from 'hooks/useLightningState';
import {
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  SnackbarProvider,
  Stack,
} from 'lightning-ui/src/design-system/components';
import ThemeProvider from 'lightning-ui/src/design-system/theme';
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { Input } from './Input';
import { postDream } from './services/api';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  image: string | null;
};

enum Links {
  stableDiffusion = 'https://stability.ai/blog/stable-diffusion-public-release',
  runYouOwnVersion = 'https://lightning.ai/app/g1VJ8GZ7XF-AI-powered%20HackerNews', // todo: replace this with actual id from spreadsheet.
  slack = 'https://join.slack.com/t/pytorch-lightning/shared_invite/zt-1dm4phlc0-84Jv9_8Mp_tWraICOJ467Q',
  twitter = 'https://twitter.com/LightningAI',
}

const shareWithUs = (domain: string) =>
  `https://twitter.com/intent/tweet?url=${domain}&text=Love+trying+out+the+new+Dream+App+on%20%40LightningAI&hashtags=BuildWithLightning`;

function Dream({ dream, image }: DreamProps) {
  if (dream && !image) {
    return <CircularProgress />;
  }
  if (image) {
    return (
      <img
        src={image}
        alt={dream || ''}
        loading="lazy"
        width="256px"
        height="256px"
        style={{ marginBottom: '40px' }}
      />
    );
  }
  return <></>;
}

function DreamSearch() {
  const { lightningState } = useLightningState();
  const [dream, setDream] = React.useState<string | null>('Cats in hats');
  const [result, setResult] = React.useState<string | null>(null);
  const [requestedDream, setRequestedDream] = React.useState('');

  const dreamIt = async () => {
    if (dream && lightningState) {
      setResult(null);
      setRequestedDream(dream);
      const result = await postDream(dream, 1, 512, lightningState.vars.dream_url);
      setResult(result['data'][0]);
    }
  };

  return (
    <Container maxWidth="sm">
      <Stack direction="column" justifyContent="center" alignItems="center" spacing={3} sx={{ marginTop: '16px' }}>
        <Stack direction="column" alignItems="center" spacing={1} textAlign={'center'}>
          <Box component={'div'} height={16} />
          <Typography variant="h4" color={theme => theme.palette.primary.main}>
            Lightning Dream Generator
          </Typography>
          <Typography variant="subtitle2" color={theme => theme.palette.primary.main}>
            Powered by{' '}
            <Link href={Links.stableDiffusion} target={'_blank'}>
              Stable Diffusion
            </Link>
          </Typography>
          <Box component={'div'} height={28} />

          <Typography variant="subtitle1" color={(theme: any) => theme.palette.grey['70']}>
            Create beautiful works of art in seconds with the Lightning Dream Generator App.
          </Typography>

          <Box component={'div'} height={16} />
          <Typography variant={'body2'}>
            {' '}
            Create art instantly |{' '}
            <Link href={Links.runYouOwnVersion} target={'_blank'}>
              {' '}
              Run your own version{' '}
            </Link>{' '}
            | Build a{' '}
            <Link href={Links.slack} target={'_blank'}>
              {' '}
              Slack{' '}
            </Link>{' '}
            or{' '}
            <Link href={Links.twitter} target={'_blank'}>
              {' '}
              Twitter{' '}
            </Link>{' '}
            Integration{' '}
          </Typography>
        </Stack>

        <Grid container spacing={1} justifyContent="center" alignItems="center">
          <Grid item xs={12} md>
            <Input value={dream} onChange={event => setDream(event.target.value)} />
          </Grid>

          <Grid item sx={{ '.MuiButton-root': { borderRadius: 40, padding: '0 30px' } }}>
            <Box component={'div'} height={{ xs: 18, md: 0 }} />
            <Button disabled={!dream} text="Dream it" onClick={dreamIt} />
          </Grid>

          <Grid item xs={12} textAlign={'center'}>
            <Box component={'div'} height={23} />
            <Typography variant={'h6'}>
              <Link href={shareWithUs(window.location.origin)} target={'_blank'}>
                Share with us
              </Link>
            </Typography>
          </Grid>
        </Grid>
        {requestedDream && <Dream dream={requestedDream} image={result} />}
      </Stack>
      <ShareWithFriends />
      <License />
    </Container>
  );
}

function App() {
  return (
    <ThemeProvider>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SnackbarProvider>
            <DreamSearch />
          </SnackbarProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;

const Typography = (props: TypographyProps) => {
  return <MuiTypography color={(theme: any) => theme.palette.grey['70']} {...props} />;
};

const License = () => {
  const [showModal, setShowModal] = useState(false);
  const onOpen = () => setShowModal(true);
  const onClose = () => setShowModal(false);
  return (
    <>
      <Dialog open={showModal}>
        <DialogTitle text="License" onClick={onClose} />
        <DialogContent>License and terms here.</DialogContent>
      </Dialog>
      <Fab
        onClick={onOpen}
        title={'License'}
        sx={{
          position: 'fixed',
          right: '20px',
          bottom: '20px',
        }}>
        <Tooltip title={'License'} placement={'top'}>
          <Notes />
        </Tooltip>
      </Fab>
    </>
  );
};

const ShareWithFriends = () => {
  const copyToClipboard = useClipboard();
  const onPress = () => {
    copyToClipboard(window.location.origin);
  };
  const theme = useTheme();
  return (
    <Box
      component={'div'}
      sx={{
        textAlign: 'center',
        [theme.breakpoints.down('sm')]: { marginBottom: '50px', marginTop: '20px' },
        [theme.breakpoints.up('sm')]: { position: 'fixed', left: 0, right: 0, bottom: '30px' },
      }}>
      <Button variant={'text'} text={'Share with a friend'} onClick={onPress} icon={<Share />} />
    </Box>
  );
};
