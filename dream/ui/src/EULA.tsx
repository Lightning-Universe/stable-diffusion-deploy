import DownloadIcon from '@mui/icons-material/Download';
import { Button, DialogContent } from '@mui/material';
import { Checkbox, Dialog, DialogActions, DialogTitle, Typography } from 'lightning-ui/src/design-system/components';
import React, { useEffect, useState } from 'react';
import { useDialogState } from './hooks/useModal';

const EULAContent = (
  props: React.ComponentProps<typeof Dialog> & {
    onAgree: () => void;
    onDisagree: () => void;
  },
) => {
  const [checked, setChecked] = useState(false);

  return (
    <Dialog {...props}>
      <DialogTitle
        text="Stability AI License Agreement"
        // TODO: fix this callback type in ds
        onClick={() => props.onClose?.('e', 'backdropClick')}
      />
      <Button startIcon={<DownloadIcon />} variant={'text'}>
        Download as PDF
      </Button>
      <DialogContent>
        <Typography>{content}</Typography>

        <Checkbox
          description={
            <Typography>
              By cecking this box lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean efficitur vestibulum
              sodales. Fusce feugiat sagittis enim, feugiat interdum ex laoreet id. Cras consectetur urna ut efficitur
              blandit.
            </Typography>
          }
          checked={checked}
          onChange={setChecked}
        />
      </DialogContent>

      <DialogActions>
        <Button onClick={props.onDisagree}>I Disagree</Button>
        <Button onClick={props.onAgree} disabled={!checked}>
          I Agree
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const content = `
By clicking the "I Agree" button, downloading or using the Application, You are agreeing to be bound by the terms and conditions of this Agreement. If You do not agree to the terms of this Agreement, do not click on the "I Agree" button, do not download or do not use the Application.

This Agreement is a legal document between You and the Company and it governs your use of the Application made available to You by the Company.

This Agreement is between You and the Company only and not with the Application Store. Therefore, the Company is solely responsible for the Application and its content. Although the Application Store is not a party to this Agreement, it has the right to enforce it against You as a third party beneficiary relating to your use of the Application.

Since the Application can be accessed and used by other users via, for example, Family Sharing / Family Group or volume purchasing, the use of the Application by those users is expressly subject to this Agreement.

The Application is licensed, not sold, to You by the Company for use strictly in accordance with the terms of this Agreement.
`;

const EULAkey = 'eula';

export const EULA: React.FC = props => {
  const dialogState = useDialogState(true);
  const [hasAcceptedTerms, acceptTerms] = useState<boolean>();
  const [showEULA, setShowEULA] = useState<boolean>();

  useEffect(() => {
    try {
      setShowEULA(JSON.parse(localStorage.getItem(EULAkey)!));
    } catch (e) {
      setShowEULA(undefined);
    }
  }, []);

  useEffect(() => {
    if (typeof hasAcceptedTerms === 'boolean') {
      if (hasAcceptedTerms) {
        localStorage.setItem(EULAkey, JSON.stringify(false));
        setShowEULA(false);
      } else {
        localStorage.setItem(EULAkey, JSON.stringify(true));
        setShowEULA(true);
      }
    }
  }, [hasAcceptedTerms]);

  if (showEULA === false) {
    return <>{props.children}</>;
  }
  if (hasAcceptedTerms === false) {
    return (
      <Dialog open={true}>
        <DialogTitle text={'Agreement Required'} />
        <DialogContent>
          <Typography>
            Sorry, but you can’t use this app without accepting the end user license agreement. Please go back and
            accept if you’d like to proceed.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              acceptTerms(undefined);
              setShowEULA(true);
            }}>
            Go Back
          </Button>
        </DialogActions>
      </Dialog>
    );
  }
  return (
    <EULAContent
      open={dialogState.open}
      // onClose={dialogState.onClose}
      onAgree={() => acceptTerms(true)}
      onDisagree={() => acceptTerms(false)}
    />
  );
};
