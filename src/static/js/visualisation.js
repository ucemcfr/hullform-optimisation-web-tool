// Create dc.js chart object and link it to div
var dataTable = dc.dataTable("#dc-table-graph"),
	lwlChart = dc.barChart("#dc-lwl-chart"),
	beamChart = dc.barChart("#dc-beam-chart"),
	draftChart = dc.barChart("#dc-draft-chart"),
	dispChart = dc.barChart("#dc-disp-chart"),
	resChart = dc.barChart("#dc-res-chart"),
	kmChart = dc.barChart("#dc-km-chart"),
	perfPlot = dc.scatterPlot("#dc-perfPlot-scatt")
	;

// Load data from CSV file
d3.csv("../static/data/design.csv", function (data) {

	// Format the data
	data.forEach(function(d) {
		d.desNum = +d["design number"];
		d.lwl = +d["LWL (m)"];
		d.beam = +d["Beam (m)"];
		d.draft = +d["Draft (m)"];
		d.disp = +d["Vol Disp (m^3)"];
		d.cwp = +d["Waterplane coefficient"];
		d.res = +d["Resistance (kN)"];
		d.km = +d["KM (m)"];
	});

	// Run the data through crossfilter
	var facts = crossfilter(data),
		all = facts.groupAll()
		;

	//Count all the facts
	dc.dataCount(".dc-data-count")
	  .dimension(facts)
	  .group(all);

	// Create dimensions
	var lwlValue = facts.dimension(function(d) {return d.lwl; }),
		beamValue = facts.dimension(function(d) {return d.beam; }),
		draftValue = facts.dimension(function(d) {return d.draft; }),
		dispValue = facts.dimension(function(d) {return d.disp; }),
		resValue = facts.dimension(function(d) {return d.res; }),
		kmValue = facts.dimension(function(d) {return d.km; })
		;

	// Create dataTable dimension
	var desNumDimension = facts.dimension(function(d) {	return [d.km, d.res]; });

	// Count and group designs
	var lwlValueGroupCount = lwlValue.group(function(d) { return Math.floor(d / 0.2) * 0.2; }), //What is this doing exactly? --> from John's "Service" code
		beamValueGroupCount = beamValue.group(function(d) { return Math.floor(d / 0.1) * 0.1; }),
		draftValueGroupCount = draftValue.group(function(d) { return Math.floor(d / 0.07) * 0.07; }),
		dispValueGroupCount = dispValue.group(function(d) { return Math.floor(d / 100) * 100; }),
		resValueGroupCount = resValue.group(function(d) { return Math.floor(d / 45) * 45; }),
		kmValueGroupCount = kmValue.group(function(d) { return Math.floor(d / 0.15) * 0.15; }),
		desGroup = desNumDimension.group(),
/*	var desGroup = desNumDimension.group().reduce(
		function reduceAdd(p,v) {
		++p.count;
		p.res += v.res;
		p.km += v.km;
		return p;
		},
		function reduceRemove(p,v) {
		--p.count;
		p.res -= v.res;
		p.km -= v.km;
		return p;
		},
		function reduceInitial() { return {}; }
		);
*/
		filteredData = desNumDimension.top(Infinity)
		;

	console.log(desGroup);

	lwlChart.width(240)
		.height(150)
		.margins({top: 10, right: 25, bottom: 20, left: 20})
		.dimension(lwlValue)
		.group(lwlValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(24)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.lwl}), d3.max(data, function(d){ return d.lwl})]))
		.elasticY(true)
		.xAxis().ticks(5);

	beamChart.width(240)
		.height(150)
		.margins({top: 10, right: 25, bottom: 20, left: 25})
		.dimension(beamValue)
		.group(beamValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(51)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.beam}), d3.max(data, function(d){ return d.beam})]))
		.elasticY(true)
		.xAxis().ticks(5);

	draftChart.width(240)
		.height(150)
		.margins({top: 10, right: 20, bottom: 20, left: 25})
		.dimension(draftValue)
		.group(draftValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(64)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.draft}), d3.max(data, function(d){ return d.draft})]))
		.elasticY(true)
		.xAxis().ticks(5);

	dispChart.width(240)
		.height(150)
		.margins({top: 10, right: 20, bottom: 20, left: 25})
		.dimension(dispValue)
		.group(dispValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(0)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.disp}), d3.max(data, function(d){ return d.disp})]))
		.elasticY(true)
		.xAxis().ticks(5);

	resChart.width(480)
		.height(150)
		//.margins({top: 10, right: 20, bottom: 20, left: 50})
		.dimension(resValue)
		.group(resValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(50)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.res}), d3.max(data, function(d){ return d.res})]))
		.elasticY(true)
		.xAxis().tickFormat();

	kmChart.width(480)
		.height(150)
		//.margins({top: 10, right: 20, bottom: 20, left: 50})
		.dimension(kmValue)
		.group(kmValueGroupCount)
		.transitionDuration(500)
		.centerBar(true)
		.gap(50)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.km}), d3.max(data, function(d){ return d.km})]))
		.elasticY(true)
		.xAxis().tickFormat();

	perfPlot.width(1000)
		.height(500)
		.x(d3.scale.linear().domain([d3.min(data, function(d){ return d.km}), d3.max(data, function(d){ return d.km})]))
		.margins({top: 10, right: 20, bottom: 50, left: 50})
		.dimension(desNumDimension)
		.group(desGroup)
		.elasticY(true)
		.elasticX(true)
		.xAxisLabel("KM (m)")
		.yAxisLabel("Resistance (kN)")
		;

	dataTable.width(960)
	.height(800)
	.dimension(desNumDimension)
	.group(function(d) {return  ""})
	.size(100)
	.columns([
	function(d) {return d.desNum; },
	function(d) {return d.lwl.toFixed(1); },
	function(d) {return d.beam.toFixed(1); },
	function(d) {return d.draft.toFixed(1); },
	function(d) {return d.disp.toFixed(0); },
	function(d) {return d.cwp.toFixed(3); },
	function(d) {return d.res.toFixed(1); },
	function(d) {return d.km.toFixed(2); }
	])
	.sortBy(function(d) {return d.desNum; })
	.order(d3.ascending);

	dc.renderAll();

});