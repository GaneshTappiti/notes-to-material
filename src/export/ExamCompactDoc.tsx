import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

export interface QAItem { id: string; question: string; answer: string; marks?: number }

const styles = StyleSheet.create({
  page: { padding: 32, fontSize: 11, fontFamily: 'Helvetica' },
  header: { fontSize: 18, marginBottom: 12, fontWeight: 600 },
  qa: { marginBottom: 10 },
  q: { fontSize: 12, fontWeight: 600 },
  a: { marginTop: 2, lineHeight: 1.3 },
  footer: { position: 'absolute', bottom: 20, left: 32, right: 32, fontSize: 9, color: '#666', textAlign: 'center' }
});

export function ExamCompactDoc({ title, footer, items }: { title: string; footer?: string; items: QAItem[] }) {
  return (
    <Document>
      <Page size="A4" style={styles.page} wrap>
        <Text style={styles.header}>{title}</Text>
        {items.map(it => (
          <View key={it.id} style={styles.qa} wrap={false}>
            <Text style={styles.q}>{it.marks ? `[${it.marks}] ` : ''}{it.question}</Text>
            <Text style={styles.a}>{it.answer}</Text>
          </View>
        ))}
        {footer && <Text style={styles.footer}>{footer}</Text>}
      </Page>
    </Document>
  );
}
