import { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  TextField,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Checkbox,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
  Grid,
  Collapse,
} from '@mui/material'
import {
  CalendarMonth as CalendarIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Description as ReportIcon,
  AutoAwesome as AIIcon,
} from '@mui/icons-material'
import axios from 'axios'

function getDefaultDateRange() {
  const now = new Date()
  const to = now.toISOString().slice(0, 10)
  const from = new Date(now)
  from.setDate(from.getDate() - 13) // 2 weeks back
  return { from: from.toISOString().slice(0, 10), to }
}

export default function CustomReport({ config, onReportGenerated }) {
  const defaultRange = getDefaultDateRange()
  const [fromDate, setFromDate] = useState(defaultRange.from)
  const [toDate, setToDate] = useState(defaultRange.to)
  const [loading, setLoading] = useState(false)
  const [threads, setThreads] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [expanded, setExpanded] = useState(null)
  const [fetchError, setFetchError] = useState(null)
  const [useAI, setUseAI] = useState(true)
  const [notes, setNotes] = useState('')
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)

  const handleFetch = async () => {
    if (!fromDate || !toDate) {
      setFetchError('Please set both From and To dates.')
      return
    }
    setFetchError(null)
    setResult(null)
    setLoading(true)
    setThreads([])
    setSelected(new Set())
    try {
      const response = await axios.get('/api/threads', {
        params: { from_date: fromDate, to_date: toDate },
      })
      setThreads(response.data.threads || [])
      if ((response.data.threads || []).length === 0) {
        setFetchError(`No daily report threads found between ${fromDate} and ${toDate}.`)
      }
    } catch (error) {
      const msg =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        error.message
      setFetchError(typeof msg === 'string' ? msg : JSON.stringify(msg))
      setThreads([])
    } finally {
      setLoading(false)
    }
  }

  const toggleSelect = (threadTs) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(threadTs)) next.delete(threadTs)
      else next.add(threadTs)
      return next
    })
  }

  const selectAll = () => {
    setSelected(new Set(threads.map((t) => t.thread_ts)))
  }

  const deselectAll = () => {
    setSelected(new Set())
  }

  const handleGenerate = async () => {
    if (selected.size === 0) {
      setResult({ success: false, error: 'Select at least one thread to include in the report.' })
      return
    }
    setGenerating(true)
    setResult(null)
    try {
      const response = await axios.post('/api/generate-from-selection', {
        thread_ts_list: Array.from(selected),
        use_ai: useAI,
        notes: notes.split('\n').filter((n) => n.trim()),
      })
      setResult(response.data)
      if (response.data.success && response.data.filename) {
        onReportGenerated(response.data.filename)
      }
    } catch (error) {
      const msg =
        error.response?.data?.error ||
        error.response?.data?.detail ||
        error.message
      setResult({
        success: false,
        error: typeof msg === 'string' ? msg : JSON.stringify(msg),
      })
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Box>
      <Typography variant="h5" className="font-bold text-gray-800 mb-4">
        Custom Report — Select Messages by Date
      </Typography>
      <Typography variant="body2" color="textSecondary" className="mb-4">
        Choose a date range to load daily report threads from Slack, then select which threads to include in the report.
      </Typography>

      <Grid container spacing={3}>
        {/* Date range & fetch */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="font-semibold mb-4">
                Date range
              </Typography>
              <Box className="space-y-3">
                <TextField
                  fullWidth
                  label="From"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <TextField
                  fullWidth
                  label="To"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  size="small"
                />
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleFetch}
                  disabled={loading || !config?.slack_configured}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
                >
                  {loading ? 'Fetching…' : 'Fetch threads'}
                </Button>
                {fetchError && (
                  <Alert severity="warning" onClose={() => setFetchError(null)}>
                    {fetchError}
                  </Alert>
                )}
              </Box>

              <Divider className="my-4" />

              <Typography variant="subtitle2" className="font-medium mb-2">
                Generate options
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={useAI}
                    onChange={(e) => setUseAI(e.target.checked)}
                    color="primary"
                    disabled={!config?.ai_configured}
                  />
                }
                label={
                  <Box className="flex items-center gap-1">
                    <AIIcon fontSize="small" />
                    Use AI enhancement
                  </Box>
                }
              />
              <TextField
                fullWidth
                label="Notes (optional)"
                multiline
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="One note per line"
                size="small"
                className="mt-2"
              />
              <Button
                fullWidth
                variant="contained"
                color="primary"
                className="mt-4"
                onClick={handleGenerate}
                disabled={generating || selected.size === 0}
                startIcon={generating ? <CircularProgress size={20} color="inherit" /> : <ReportIcon />}
              >
                {generating ? 'Generating…' : `Generate from ${selected.size} selected`}
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Thread list */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box className="flex items-center justify-between mb-4">
                <Typography variant="h6" className="font-semibold">
                  Threads in range
                </Typography>
                {threads.length > 0 && (
                  <Box className="flex gap-2">
                    <Button size="small" onClick={selectAll}>
                      Select all
                    </Button>
                    <Button size="small" onClick={deselectAll}>
                      Deselect all
                    </Button>
                  </Box>
                )}
              </Box>

              {threads.length === 0 && !loading && (
                <Box className="text-center py-8 text-gray-500">
                  <CalendarIcon sx={{ fontSize: 48 }} className="mb-2" />
                  <Typography>Set dates and click &quot;Fetch threads&quot; to load daily report threads.</Typography>
                </Box>
              )}

              <List disablePadding>
                {threads.map((t) => (
                  <Box key={t.thread_ts}>
                    <ListItem disablePadding divider>
                      <ListItemButton
                        onClick={() => toggleSelect(t.thread_ts)}
                        dense
                      >
                        <ListItemIcon>
                          <Checkbox
                            edge="start"
                            checked={selected.has(t.thread_ts)}
                            tabIndex={-1}
                            disableRipple
                          />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box className="flex items-center gap-2 flex-wrap">
                              <Typography variant="body2" fontWeight="medium">
                                {t.date}
                              </Typography>
                              <Chip label={`${t.reply_count} replies`} size="small" variant="outlined" />
                              <Typography variant="caption" color="textSecondary">
                                by {t.posted_by}
                              </Typography>
                            </Box>
                          }
                          secondary={
                            <Typography
                              variant="body2"
                              color="textSecondary"
                              className="mt-1"
                              sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
                            >
                              {(t.header_text || '').replace(/\*/g, '').slice(0, 200)}
                              {(t.header_text || '').length > 200 ? '…' : ''}
                            </Typography>
                          }
                        />
                        {t.reply_preview && t.reply_preview.length > 0 && (
                          <Button
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation()
                              setExpanded(expanded === t.thread_ts ? null : t.thread_ts)
                            }}
                            endIcon={expanded === t.thread_ts ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                          >
                            {expanded === t.thread_ts ? 'Hide' : 'Preview'}
                          </Button>
                        )}
                      </ListItemButton>
                    </ListItem>
                    {t.reply_preview && t.reply_preview.length > 0 && (
                      <Collapse in={expanded === t.thread_ts} timeout="auto" unmountOnExit>
                        <Box className="pl-4 pr-4 pb-2 pt-0">
                          {t.reply_preview.map((r, i) => (
                            <Box key={i} className="mb-2 p-2 bg-gray-50 rounded">
                              <Typography variant="caption" color="primary" fontWeight="medium">
                                {r.user}
                              </Typography>
                              <Typography variant="body2" color="textSecondary">
                                {r.text_snippet}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Collapse>
                    )}
                  </Box>
                ))}
              </List>

              {/* Result */}
              {result && (
                <Box className="mt-4">
                  <Divider className="mb-4" />
                  {result.success ? (
                    <>
                      <Alert severity="success" icon={<CheckIcon />} className="mb-4">
                        <Typography variant="subtitle1" fontWeight="bold">
                          Report generated
                        </Typography>
                        <Typography variant="body2">
                          Saved as: {result.filename} • {result.date_range}
                        </Typography>
                        {result.stats && (
                          <Box className="flex gap-2 mt-2">
                            <Chip label={`${result.stats.threads_included || 0} threads`} size="small" />
                            <Chip label={`${result.stats.status_messages || 0} messages`} size="small" />
                          </Box>
                        )}
                      </Alert>
                      <Typography variant="subtitle2" className="font-medium mb-2">
                        Preview
                      </Typography>
                      <Box
                        className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-80 overflow-auto"
                        sx={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}
                      >
                        {result.report}
                      </Box>
                    </>
                  ) : (
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <Typography variant="subtitle1" fontWeight="bold">
                        Failed to generate report
                      </Typography>
                      <Typography variant="body2">{result.error}</Typography>
                    </Alert>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
