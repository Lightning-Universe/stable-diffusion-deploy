import { styled } from '@mui/material/styles';
import MuiSwitch from '@mui/material/Switch';

const SIZE = 16;

export const Switch = styled(MuiSwitch)(({ theme, disabled }) => ({
  'opacity': disabled ? 0.5 : 1,
  'width': SIZE * 2 + 4,
  'height': SIZE + 4,
  'padding': 0,
  'display': 'flex',
  '& .MuiSwitch-switchBase': {
    'padding': 2,
    '&.Mui-checked': {
      'padding': 0,
      'transform': `translateX(${SIZE}px)`,
      'color': '#FFF',
      '& + .MuiSwitch-track': {
        opacity: 1,
        backgroundColor: '#D6CEF5',
      },
    },
  },
  '& .Mui-checked .MuiSwitch-thumb': {
    width: SIZE + 4,
    height: SIZE + 4,
    background: 'linear-gradient(206.91deg, #792EE5 16.83%, #3EABB3 144.59%)',
  },
  '& .MuiSwitch-thumb': {
    width: SIZE,
    height: SIZE,
    borderRadius: SIZE,
    boxShadow: '0 2px 4px 0 rgb(0 35 11 / 20%)',

    background: '#65676B',
    transition: theme.transitions.create(['width'], {
      duration: 150,
    }),
  },
  '& .MuiSwitch-track': {
    borderRadius: (SIZE + 4) / 2,
    opacity: 1,
    backgroundColor: 'rgba(0,0,0,.25)',
    boxSizing: 'border-box',
  },
}));
