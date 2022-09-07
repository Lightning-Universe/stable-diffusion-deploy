import { Share } from '@mui/icons-material';
import {
  Box,
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
import { Button, SnackbarProvider, Stack } from 'lightning-ui/src/design-system/components';
import ThemeProvider from 'lightning-ui/src/design-system/theme';
import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { Input } from './Input';
import { ProgressBar } from './Loader';
import { postDream } from './services/api';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  image: string | null;
};

enum Links {
  stableDiffusion = 'https://stability.ai/blog/stable-diffusion-public-release',
  runYouOwnVersion = 'https://lightning.ai/app/g1VJ8GZ7XF-AI-powered%20HackerNews', // todo: replace this with actual id from spreadsheet.
  slack = 'https://wsvbs-01gbz6hpp0nx2ahp49ect17q2n.litng-ai-03.litng.ai/slack/start',
  twitter = 'https://twitter.com/LightningAI',
}

const shareWithUs = (domain: string) =>
  `https://twitter.com/intent/tweet?url=${domain}&text=Love+trying+out+the+new+Dream+App+on%20%40LightningAI&hashtags=BuildWithLightning`;

function Dream({ dream, image }: DreamProps) {
  if (dream && !image) {
    return <ProgressBar />;
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
      setResult(result[0]);
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
          <SlackOAuthLink />
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

const ShareWithFriends = () => {
  const copyToClipboard = useClipboard();
  const onPress = () => {
    copyToClipboard(window.location.origin);
  };
  return (
    <Fab onClick={onPress} title={'Share with friends'} sx={{ position: 'fixed', right: '20px', bottom: '20px' }}>
      <Tooltip title={'Share with friends'} placement={'top'}>
        <Share />
      </Tooltip>
    </Fab>
  );
};

const License = () => {
  const theme = useTheme();
  return (
    <Box
      component={'div'}
      sx={{
        textAlign: 'center',
        [theme.breakpoints.down('sm')]: { marginBottom: '50px', marginTop: '20px' },
        [theme.breakpoints.up('sm')]: { position: 'fixed', left: 0, right: 0, bottom: '30px' },
      }}>
      <Typography variant="caption">
        <Link href={'https://huggingface.co/spaces/CompVis/stable-diffusion-license'} target={'_blank'}>
          License of usage
        </Link>
      </Typography>
    </Box>
  );
};

const SlackOAuthLink = () => {
  return (
    <a href={Links.slack} target={'_blank'} rel="noreferrer">
      <img
        alt="Add to Slack"
        height="40"
        width="139"
        src="https://platform.slack-edge.com/img/add_to_slack.png"
        srcSet="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x"
      />
    </a>
  );
};
