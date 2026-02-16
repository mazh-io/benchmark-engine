import type { Metadata } from 'next';
import { LegalShell } from '@/templates/legal/LegalShell';

export const metadata: Metadata = {
  title: 'Impressum — MAZH',
};

export default function ImprintPage() {
  return (
    <LegalShell title="Impressum" lastUpdated="Angaben gem&auml;&szlig; &sect; 5 TMG">
      <div className="legal-placeholder">
        <p>
          📋 <strong>Placeholder</strong> – Bitte die tats&auml;chlichen
          Unternehmensdaten eintragen.
        </p>
      </div>

      <div className="imprint-block">
        <h3>Anbieter</h3>
        <p><strong>skot UG (haftungsbeschr&auml;nkt)</strong></p>
        <p>[Stra&szlig;e Hausnummer]</p>
        <p>[PLZ Stadt]</p>
        <p>Deutschland</p>
      </div>

      <div className="imprint-block">
        <h3>Vertreten durch</h3>
        <p>Gesch&auml;ftsf&uuml;hrer: [Vollst&auml;ndiger Name]</p>
      </div>

      <div className="imprint-block">
        <h3>Kontakt</h3>
        <p>E-Mail: <a href="mailto:hello@skot.io">hello@skot.io</a></p>
        <p>Telefon: [Telefonnummer]</p>
      </div>

      <div className="imprint-block">
        <h3>Registereintrag</h3>
        <p>Registergericht: Amtsgericht [Stadt]</p>
        <p>Registernummer: HRB [Nummer]</p>
      </div>

      <div className="imprint-block">
        <h3>Umsatzsteuer-ID</h3>
        <p>
          Umsatzsteuer-Identifikationsnummer gem&auml;&szlig; &sect; 27a UStG:
        </p>
        <p>DE [Nummer]</p>
      </div>

      <h2>Verantwortlich f&uuml;r den Inhalt nach &sect; 55 Abs. 2 RStV</h2>
      <p>
        [Vollst&auml;ndiger Name]<br />
        [Stra&szlig;e Hausnummer]<br />
        [PLZ Stadt]
      </p>

      <h2>Streitschlichtung</h2>
      <p>
        Die Europ&auml;ische Kommission stellt eine Plattform zur
        Online-Streitbeilegung (OS) bereit:{' '}
        <a
          href="https://ec.europa.eu/consumers/odr/"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://ec.europa.eu/consumers/odr/
        </a>
      </p>
      <p>Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>
      <p>
        Wir sind nicht bereit oder verpflichtet, an
        Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle
        teilzunehmen.
      </p>

      <h2>Haftung f&uuml;r Inhalte</h2>
      <p>
        Als Diensteanbieter sind wir gem&auml;&szlig; &sect; 7 Abs.1 TMG
        f&uuml;r eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen
        verantwortlich. Nach &sect;&sect; 8 bis 10 TMG sind wir als
        Diensteanbieter jedoch nicht verpflichtet, &uuml;bermittelte oder
        gespeicherte fremde Informationen zu &uuml;berwachen oder nach
        Umst&auml;nden zu forschen, die auf eine rechtswidrige T&auml;tigkeit
        hinweisen.
      </p>

      <h2>Haftung f&uuml;r Links</h2>
      <p>
        Unser Angebot enth&auml;lt Links zu externen Websites Dritter, auf
        deren Inhalte wir keinen Einfluss haben. Deshalb k&ouml;nnen wir
        f&uuml;r diese fremden Inhalte auch keine Gew&auml;hr &uuml;bernehmen.
        F&uuml;r die Inhalte der verlinkten Seiten ist stets der jeweilige
        Anbieter oder Betreiber der Seiten verantwortlich.
      </p>

      <h2>Urheberrecht</h2>
      <p>
        Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen
        Seiten unterliegen dem deutschen Urheberrecht. Die
        Vervielf&auml;ltigung, Bearbeitung, Verbreitung und jede Art der
        Verwertung au&szlig;erhalb der Grenzen des Urheberrechtes bed&uuml;rfen
        der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
      </p>
    </LegalShell>
  );
}
