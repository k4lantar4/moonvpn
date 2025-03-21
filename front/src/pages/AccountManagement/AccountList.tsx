import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  useTheme,
} from '@mui/material';
import { useTranslation } from 'react-i18next';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import QrCodeIcon from '@mui/icons-material/QrCode';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';

// Example data - replace with actual API data
const accounts = [
  {
    id: 1,
    name: 'Account 1',
    status: 'active',
    expiryDate: '2024-04-01',
    trafficUsed: 25,
    trafficLimit: 50,
    configUrl: 'vmess://example.com',
    protocol: 'vmess',
    server: 'Server 1',
  },
  {
    id: 2,
    name: 'Account 2',
    status: 'active',
    expiryDate: '2024-04-15',
    trafficUsed: 75,
    trafficLimit: 100,
    configUrl: 'vmess://example.com',
    protocol: 'vmess',
    server: 'Server 2',
  },
];

const AccountList: React.FC = () => {
  const theme = useTheme();
  const { t } = useTranslation();
  const [selectedAccount, setSelectedAccount] = useState<any>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [accountName, setAccountName] = useState('');

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return theme.palette.success.main;
      case 'expired':
        return theme.palette.error.main;
      case 'suspended':
        return theme.palette.warning.main;
      default:
        return theme.palette.text.secondary;
    }
  };

  const handleEditClick = (account: any) => {
    setSelectedAccount(account);
    setAccountName(account.name);
    setEditDialogOpen(true);
  };

  const handleDeleteClick = (account: any) => {
    setSelectedAccount(account);
    setDeleteDialogOpen(true);
  };

  const handleEditSave = () => {
    // TODO: Implement API call to update account name
    setEditDialogOpen(false);
  };

  const handleDeleteConfirm = () => {
    // TODO: Implement API call to delete account
    setDeleteDialogOpen(false);
  };

  return (
    <Box>
      <Grid container spacing={2}>
        {accounts.map((account) => (
          <Grid item xs={12} md={6} key={account.id}>
            <Card
              sx={{
                backgroundColor: theme.palette.background.paper,
                border: `1px solid ${theme.palette.divider}`,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" sx={{ color: theme.palette.text.primary }}>
                    {account.name}
                  </Typography>
                  <Box>
                    <Tooltip title={t('account_management.copy_config')}>
                      <IconButton
                        size="small"
                        onClick={() => copyToClipboard(account.configUrl)}
                      >
                        <ContentCopyIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('account_management.show_qr')}>
                      <IconButton size="small">
                        <QrCodeIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('account_management.refresh')}>
                      <IconButton size="small">
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('account_management.edit')}>
                      <IconButton
                        size="small"
                        onClick={() => handleEditClick(account)}
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title={t('account_management.delete')}>
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteClick(account)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      color: getStatusColor(account.status),
                      display: 'inline-block',
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      backgroundColor: `${getStatusColor(account.status)}20`,
                    }}
                  >
                    {t(`account_management.status.${account.status}`)}
                  </Typography>
                </Box>

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {t('account_management.server')}: {account.server}
                  </Typography>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {t('account_management.protocol')}: {account.protocol}
                  </Typography>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {t('account_management.expiry_date')}: {new Date(account.expiryDate).toLocaleDateString('fa-IR')}
                  </Typography>
                </Box>

                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                    {t('account_management.traffic_usage')}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={(account.trafficUsed / account.trafficLimit) * 100}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: theme.palette.background.default,
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: theme.palette.primary.main,
                      },
                    }}
                  />
                </Box>

                <Typography variant="body2" sx={{ color: theme.palette.text.secondary }}>
                  {account.trafficUsed} / {account.trafficLimit} GB
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Edit Account Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)}>
        <DialogTitle>{t('account_management.edit_account')}</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label={t('account_management.account_name')}
            fullWidth
            value={accountName}
            onChange={(e) => setAccountName(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleEditSave} variant="contained">
            {t('common.save')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>{t('account_management.delete_account')}</DialogTitle>
        <DialogContent>
          <Typography>
            {t('account_management.delete_confirm', { name: selectedAccount?.name })}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            {t('common.cancel')}
          </Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            {t('common.delete')}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountList; 