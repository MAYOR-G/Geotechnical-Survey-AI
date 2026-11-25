// ============================================================================
// MASTER TYPST TEMPLATE: GEOTECHNICAL SITE, HDD & LABORATORY INVESTIGATION REPORT
// ============================================================================

#let render-hdd-report(
  client-name: "Client / Operator",
  contractor-name: "Lead Geotechnical Contractor",
  consultant-name: "Geotechnical Engineering Consultant",
  program-title: "GEOTECHNICAL ENGINEERING DELIVERABLE",
  report-title: "GEOTECHNICAL SITE & LABORATORY INVESTIGATION REPORT",
  report-subtitle: "FINAL INTERPRETATIVE AND FACTUAL REPORT",
  client-ref: "DOC-REF-001",
  contractor-ref: "DOC-REF-001",
  revision-number: "Rev 01",
  fao-text: "Engineering Directorate",
  client-logo: none,
  contractor-logo: none,
  partner-logo: none,
  signature-img: none,
  revision-rows: (),
  auth-prepared: (:),
  auth-reviewed: (:),
  auth-approved1: (:),
  auth-approved2: (:),
  body-content: [],
) = {
  set document(title: report-title, author: contractor-name)
  set text(font: ("Helvetica Neue", "Arial", "Liberation Sans"), size: 10pt, fill: rgb("#1D1D1F"))
  set par(justify: true, leading: 0.68em, spacing: 1.02em)
  set heading(numbering: none)
  show figure.where(kind: table): set block(breakable: true)
  show figure.where(kind: table): set figure.caption(position: top)
  show figure.where(kind: image): set block(breakable: false)

  show heading.where(level: 1): it => block(
    above: 1.8em,
    below: 0.85em,
    breakable: false,
    sticky: true,
    stroke: (bottom: 0.9pt + rgb("#0066CC")),
    inset: (bottom: 5pt),
    text(size: 12.8pt, weight: "bold", fill: rgb("#1D1D1F"), upper(it.body))
  )

  show heading.where(level: 2): it => block(
    above: 1.3em,
    below: 0.6em,
    breakable: false,
    sticky: true,
    text(size: 11pt, weight: "bold", fill: rgb("#1D1D1F"), it.body)
  )

  show heading.where(level: 3): it => block(
    above: 1.0em,
    below: 0.5em,
    breakable: false,
    sticky: true,
    text(size: 10.2pt, weight: "bold", fill: rgb("#333333"), it.body)
  )

  let running-header() = {
    table(
      columns: (50%, 50%),
      stroke: 0.6pt + rgb("#1D1D1F"),
      inset: (x: 8pt, y: 5pt),
      align: (left + horizon, right + horizon),
      if client-logo != none {
        image(client-logo, height: 24pt, fit: "contain")
      } else {
        text(weight: "bold", size: 8.8pt, client-name)
      },
      grid(
        columns: (auto, auto),
        gutter: 10pt,
        align: right + horizon,
        if contractor-logo != none {
          image(contractor-logo, height: 22pt, fit: "contain")
        } else {
          text(weight: "bold", size: 8.8pt, contractor-name)
        },
        if partner-logo != none {
          image(partner-logo, height: 18pt, fit: "contain")
        } else {
          []
        }
      )
    )
  }

  let running-footer() = {
    line(length: 100%, stroke: 0.5pt + rgb("#E0E0E0"))
    v(3pt)
    grid(
      columns: (1fr, auto),
      text(size: 8pt, fill: rgb("#4B5565"), contractor-ref + "  |  " + contractor-name),
      text(size: 8pt, weight: "bold", fill: rgb("#1D1D1F"), [
        Page #context counter(page).display("1 of 1", both: true)
      ])
    )
  }

  // ==========================================================================
  // PAGE 1: DEDICATED CORPORATE COVER & REVISION CONTROL PAGE
  // ==========================================================================
  page(
    paper: "a4",
    margin: (top: 1.6cm, bottom: 1.6cm, left: 1.8cm, right: 1.8cm),
    header: none,
    footer: none,
  )[
    #rect(width: 100%, height: 100%, stroke: 0.9pt + rgb("#1D1D1F"), inset: 0pt)[
      #grid(
        rows: (auto, auto, 1fr, auto, auto, auto),
        running-header(),
        block(
          width: 100%,
          fill: rgb("#F5F5F7"),
          stroke: (bottom: 0.6pt + rgb("#1D1D1F")),
          inset: (y: 7pt, x: 12pt),
          align(center)[#text(size: 9.5pt, weight: "bold", font: "Courier New", contractor-ref)]
        ),
        align(center + horizon)[
          #pad(x: 24pt)[
            #text(size: 12.5pt, weight: "bold", fill: rgb("#0066CC"), upper(program-title))
            #v(14pt)
            #text(size: 18.5pt, weight: "bold", fill: rgb("#1D1D1F"), upper(report-title))
            #v(10pt)
            #text(size: 13pt, weight: "bold", fill: rgb("#333333"), report-subtitle)
            #v(16pt)
            #text(size: 10.5pt, weight: "bold", fill: rgb("#1D1D1F"), [Prepared by: #contractor-name]) \
            #v(4pt)
            #text(size: 10pt, fill: rgb("#4B5565"), [Client / Operator: #client-name])
          ]
        ],
        block(
          width: 100%,
          stroke: (top: 0.7pt + rgb("#1D1D1F"), bottom: 0.7pt + rgb("#1D1D1F")),
          inset: (y: 8pt),
          align(center)[#text(size: 11pt, weight: "bold", [Revision: #revision-number])]
        ),
        table(
          columns: (10%, 15%, 36%, 13%, 13%, 13%),
          stroke: 0.6pt + rgb("#1D1D1F"),
          inset: 5pt,
          align: center + horizon,
          table.cell(fill: rgb("#F5F5F7"))[*Rev*],
          table.cell(fill: rgb("#F5F5F7"))[*Date*],
          table.cell(fill: rgb("#F5F5F7"))[*Description*],
          table.cell(fill: rgb("#F5F5F7"))[*Prepared*],
          table.cell(fill: rgb("#F5F5F7"))[*Checked*],
          table.cell(fill: rgb("#F5F5F7"))[*Approved*],
          ..revision-rows.flatten(),
        ),
        block(
          width: 100%,
          inset: 9pt,
          text(size: 8pt, fill: rgb("#333333"), [
            Proprietary Engineering Deliverable prepared by #contractor-name for #client-name. Neither the whole nor any part of this document may be reproduced or disclosed to third parties without prior written consent.
          ])
        )
      )
    ]
  ]

  // ==========================================================================
  // PAGE 2+: RUNNING CORPORATE HEADER & FOOTER
  // ==========================================================================
  set page(
    paper: "a4",
    margin: (top: 2.8cm, bottom: 2.2cm, left: 2.0cm, right: 2.0cm),
    header: running-header(),
    footer: running-footer(),
  )

  heading(level: 1, outlined: false)[DOCUMENT AUTHORISATION AND QUALITY CONTROL]
  table(
    columns: (18%, 24%, 22%, 20%, 16%),
    stroke: 0.6pt + rgb("#1D1D1F"),
    inset: 6pt,
    table.header(
      table.cell(fill: rgb("#F5F5F7"))[*Role*],
      table.cell(fill: rgb("#F5F5F7"))[*Name*],
      table.cell(fill: rgb("#F5F5F7"))[*Designation*],
      table.cell(fill: rgb("#F5F5F7"))[*Signature*],
      table.cell(fill: rgb("#F5F5F7"))[*Date*],
    ),
    [*Prepared By*],
    [#auth-prepared.at("name", default: "Lead Geotechnical Engineer")],
    [#auth-prepared.at("designation", default: "Lead Geotechnical Engineer")],
    if signature-img != none { image(signature-img, height: 18pt, fit: "contain") } else { [—] },
    [#auth-prepared.at("date", default: "2026")],
    [*Checked By*],
    [#auth-reviewed.at("name", default: "Principal Reviewer")],
    [#auth-reviewed.at("designation", default: "Principal Geoscientist")],
    [—],
    [#auth-reviewed.at("date", default: "2026")],
    [*Approved By*],
    [#auth-approved1.at("name", default: "Technical Director")],
    [#auth-approved1.at("designation", default: "Technical Director")],
    [—],
    [#auth-approved1.at("date", default: "2026")],
  )

  v(14pt)
  outline(title: [TABLE OF CONTENTS], indent: auto, depth: 2)
  v(14pt)
  outline(title: [LIST OF TABLES], target: figure.where(kind: table))
  v(14pt)
  outline(title: [LIST OF FIGURES], target: figure.where(kind: image))

  pagebreak()

  // MAIN REPORT BODY
  body-content
}
