import React, { useState } from 'react';
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import AccountList from './AccountList';
import CreateAccount from './CreateAccount';
import AccountHistory from './AccountHistory';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`account-tabpanel-${index}`}
      aria-labelledby={`account-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AccountManagement: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Box>
      <Paper
        sx={{
          backgroundColor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        <Tabs
          value={value}
          onChange={handleChange}
          aria-label="account management tabs"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 500,
            },
          }}
        >
          <Tab
            label={t('account_management.tabs.accounts')}
            id="account-tab-0"
            aria-controls="account-tabpanel-0"
          />
          <Tab
            label={t('account_management.tabs.create')}
            id="account-tab-1"
            aria-controls="account-tabpanel-1"
          />
          <Tab
            label={t('account_management.tabs.history')}
            id="account-tab-2"
            aria-controls="account-tabpanel-2"
          />
        </Tabs>

        <TabPanel value={value} index={0}>
          <AccountList />
        </TabPanel>
        <TabPanel value={value} index={1}>
          <CreateAccount />
        </TabPanel>
        <TabPanel value={value} index={2}>
          <AccountHistory />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default AccountManagement; 