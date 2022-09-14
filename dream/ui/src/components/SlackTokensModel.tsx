import { Box, Button as MuiButton, Link } from '@mui/material';
import { Button, Dialog, DialogContent, DialogTitle, TextField } from 'lightning-ui/src/design-system/components';
import { useEffect, useState } from 'react';
import { setSlackCredentials, SlackForm } from '../services/api';
import { LightingState } from '../types/lightning';
import { Typography } from './Typography';

const SlackTokensModel = (props: { isModalOpen: boolean; url: string; setModalOpen: (e: boolean) => void }) => {
  const [formData, setFormData] = useState<{
    [key in SlackForm]: string;
  }>({
    [SlackForm._signing_secret]: '',
    [SlackForm._bot_token]: '',
    [SlackForm._slack_client_id]: '',
    [SlackForm._client_secret]: '',
    [SlackForm._slack_token]: '',
  });

  const setValue = (key: SlackForm) => (value: string | null) => {
    if (value === null) return;
    setFormData(x => ({ ...x, [key]: value }));
  };
  const hasAllValues = () => Object.values(formData).every(e => !!e);

  const onSubmit = async () => {
    if (!hasAllValues()) return;
    console.log('submit form', formData);
    setSlackCredentials(formData, props.url);
    props.setModalOpen(false);
  };
  return (
    <Dialog open={props.isModalOpen} onClose={() => props.setModalOpen(false)}>
      <DialogTitle text={'Add token'} onClick={() => props.setModalOpen(false)} />
      <DialogContent>
        <Box sx={{ minWidth: '320px' }}>
          <Typography>
            Get the credentials by following <Link>these steps</Link>
          </Typography>
          <TextField
            value={formData.SIGNING_SECRET}
            onChange={setValue(SlackForm._signing_secret)}
            label={'signing secret'}
            placeholder={'********'}
            fullWidth
          />
          <TextField
            value={formData.BOT_TOKEN}
            onChange={setValue(SlackForm._bot_token)}
            label={'bot token'}
            placeholder={'********'}
            fullWidth
          />
          <TextField
            value={formData.SLACK_CLIENT_ID}
            onChange={setValue(SlackForm._slack_client_id)}
            label={'slack client id'}
            placeholder={'********'}
            fullWidth
          />
          <TextField
            value={formData.CLIENT_SECRET}
            onChange={setValue(SlackForm._client_secret)}
            label={'client secret'}
            placeholder={'********'}
            fullWidth
          />
          <TextField
            value={formData.SLACK_TOKEN}
            onChange={setValue(SlackForm._slack_token)}
            label={'Slack token'}
            placeholder={'********'}
            fullWidth
          />
          <br />
          <br />
          <Button text={'Submit'} disabled={!hasAllValues()} onClick={onSubmit} fullWidth />
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export const AddYourSlackCredentials = (props: LightingState) => {
  const [isModalOpen, setModalOpen] = useState<boolean>(false);
  const has_credentials: string | undefined = props?.works?.slack_bot?.vars?.has_credentials;
  useEffect(() => {
    if (typeof has_credentials !== 'undefined') {
      setModalOpen(!has_credentials);
    }
  }, [has_credentials]);

  return (
    <>
      <SlackTokensModel isModalOpen={isModalOpen} url={props?.vars?.slack_bot_url} setModalOpen={setModalOpen} />
      {typeof has_credentials === 'boolean' && !has_credentials && (
        <MuiButton variant={'text'} onClick={() => setModalOpen(true)}>
          Add your own slack credentials
        </MuiButton>
      )}
    </>
  );
};
