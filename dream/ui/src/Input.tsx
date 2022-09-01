import { OutlinedInput, OutlinedInputProps } from 'lightning-ui/src/design-system/components';

export const Input = (props: OutlinedInputProps) => {
  return (
    <OutlinedInput
      {...props}
      fullWidth
      placeholder="Cats in hats"
      sx={{
        'fontFamily': 'Roboto',
        'fontStyle': 'normal',
        'fontWeight': 'normal',
        'fontSize': '14px',
        'lineHeight': '20px',
        'height': '36px',
        'backgroundColor': 'white',
        'borderRadius': '26px',
        '&.MuiInputBase-colorPrimary:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: (theme: any) => theme.palette['primary'].main,
        },
        '&.Mui-error .MuiOutlinedInput-notchedOutline': {
          padding: 0,
        },
        '&.Mui-disabled': {
          backgroundColor: (theme: any) => theme.palette.grey['10'],
        },
        '&.Mui-disabled:hover .MuiOutlinedInput-notchedOutline': {
          borderColor: 'rgba(0,0,0,0.26)',
        },
        '&.Mui-error.Mui-disabled .MuiOutlinedInput-notchedOutline': {
          borderColor: 'rgba(0,0,0,0.26)',
        },
        '&.Mui-disabled .MuiOutlinedInput-input': {
          color: (theme: any) => theme.palette.grey['20'],
        },
        '&.MuiInputBase-sizeSmall': {
          height: '28px',
        },
      }}
    />
  );
};
