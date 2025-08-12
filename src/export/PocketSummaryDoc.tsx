import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';
import { trimToSentence } from '@/lib/utils';
import type { QAItem } from './ExamCompactDoc';

const styles = StyleSheet.create({
  page: { padding: 28, fontSize: 10, fontFamily: 'Helvetica' },
  header: { fontSize: 16, marginBottom: 10, fontWeight: 600 },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  card: { width: '48%', marginRight: '4%', marginBottom: 10 },
  lastInRow: { marginRight: 0 },
  q: { fontSize: 10, fontWeight: 600 },
  a: { marginTop: 2, lineHeight: 1.2 },
  footer: { position: 'absolute', bottom: 16, left: 28, right: 28, fontSize: 8, color: '#666', textAlign: 'center' }
});

export function PocketSummaryDoc({ title, footer, items, maxAnswerChars = 180 }: { title: string; footer?: string; items: QAItem[]; maxAnswerChars?: number }) {
  return (
    <Document>
      <Page size="A4" style={styles.page} wrap>
        <Text style={styles.header}>{title} — Pocket</Text>
        <View style={styles.grid}>
          {items.map((it, idx) => {
            const shortAns = trimToSentence(it.answer, maxAnswerChars);
            const isLastInRow = (idx % 2) === 1;
            return (
              <View key={it.id} style={[styles.card, isLastInRow && styles.lastInRow]} wrap={false}>
                <Text style={styles.q}>{it.question}</Text>
                <Text style={styles.a}>{shortAns}</Text>
              </View>
            );
          })}
        </View>
        {footer && <Text style={styles.footer}>{footer}</Text>}
      </Page>
    </Document>
  );
}
