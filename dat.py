#!/usr/bin/python

import sys
import array
import struct

class dat:
	def __init__(self,filename):
		self.gene_list=[]
		self.gene_table={}
		self.open_file(filename)
		self.gene_index={}
		for i in range(len(self.gene_list)):
			self.gene_index[self.gene_list[i]]=i

	def open_file(self,filename):
		dab_file = open(filename, 'rb' )

		#get number of genes
		a = array.array('I')
		a.fromfile(dab_file,1)
		size=a[0]

		#get gene names
		start=4
		end=4
		count=0
		while count < a[0]:
			dab_file.seek(end)
			if( dab_file.read(2)=='\0\0' ):
				dab_file.seek(start)

				gene = dab_file.read(end-start+1)
				gene = gene.strip()
				gene = gene.replace('\x00','')

				self.gene_list.append(gene)
				self.gene_table[gene]=count

				start=end+2
				count+=1
				end+=1
			end+=1

		#get half matrix values
		total=(size*(size-1))/2
		dab_file.seek(start)
		self.dat = array.array('f')
		self.dat.fromfile(dab_file,total)

		assert len(self.dat) == total

	def get_size(self):
		return len(self.gene_list)

	def get_gene(self, id):
		return self.gene_list[id]

	def get_value(self, gene1, gene2):
		g1 = min( gene1, gene2 )
		g2 = max( gene1, gene2 )

		start=self.arith_sum( (len(self.gene_list))-g1, (len(self.gene_list)-1) ) #index of first id
		start += (g2-g1)-1 #index of second id
		try:
			v= self.dat[int(start)]
		except IndexError:
			print 'Error: ', start, gene1, gene2
			exit()

		return v

        def get_scaled_value(self, gene1, gene2, prior_new, prior_old):
            r = prior_new / prior_old
            r_diff = (1-prior_new) / (1-prior_old)
            weight = self.get_value(gene1, gene2)
            return (weight * r) / (weight * r + (1-weight) * r_diff)

        def get_index(self, gene):
		try:
			return self.gene_index[gene]
		except KeyError:
			return None	

	def arith_sum(self, x, y ):
		return .5 * (y-x+1) * (x+y)

	def print_table(self, out_file=sys.stdout):
		cols = ['GENE']
		cols.extend(self.gene_list) 
		print >> out_file, "\t".join(cols)

		for i in range(0,self.get_size()):
			line=[]
			line.append(self.gene_list[i])
			for j in range(0,i):
				v = self.get_value(i,j)
				line.append(str(v))
			line.append("1")
			for j in range(i+1,self.get_size()):
                                v = self.get_value(i,j) 
                                line.append(str(v))

			print >> out_file, "\t".join(line)

	def print_flat(self, out_file=sys.stdout):
		for i in range(0,self.get_size()):
			for j in range(i+1, self.get_size()):
				print >> out_file, self.gene_list[i] + '\t' + self.gene_list[j] + '\t' + str(self.get_value(i, j))


	def get_neighbors(self, gene_str, cutoff):
		neighbors = set()
		gene_id = self.get_index(gene_str)
		if gene_id is None:
			return neighbors
		for i in range(0,len(self.gene_list)):
			if self.get_value(gene_id, i) > cutoff:
				neighbors.add(self.gene_list[i]) 
		return neighbors

        def get_all_neighbor_vals(self, gene_id):
            vals = list()
            #gene_id = self.get_index(gene_str)
            if gene_id is None:
                return vals

            for i in xrange(gene_id):
                vals.append(self.get_value(gene_id, i))
            for i in xrange(gene_id+1, self.get_size()):
                vals.append(self.get_value(gene_id, i))

            return vals


        def get_all_scaled_neighbor_vals(self, gene_id, prior_new, prior_old):
            vals = list()
            if gene_id is None:
                return vals

            for i in xrange(gene_id):
                vals.append(self.get_scaled_value(gene_id, i, prior_new, prior_old))
            for i in xrange(gene_id+1, self.get_size()):
                vals.append(self.get_scaled_value(gene_id, i, prior_new, prior_old))

            return vals

        def get_all_neighbor_val_dict(self, gene_id):
            n_vals = dict()

            if gene_id is None:
                return n_vals

            for i in xrange(gene_id):
                n_vals[i] = self.get_value(gene_id, i)
            for i in xrange(gene_id+1, self.get_size()):
                n_vals[i] = self.get_value(gene_id, i)

            return n_vals

        def get(self, gene_str):
		vals = []
		idx = self.get_index(gene_str)
		if idx is None:
                    return vals
		for i in range(0,idx):
                    start = self.arith_sum( (len(self.gene_list))-i, (len(self.gene_list)-1) )
                    start += (idx-i)-1
                    v = self.dat[int(start)]
                    vals.append(v)
                start = self.arith_sum( (len(self.gene_list))-idx, (len(self.gene_list)-1) )
                start -= 1
                vals += self.dat[int(start):int(start)+len(self.gene_list)-idx]

                return vals


if __name__ == '__main__':
	from optparse import OptionParser

	usage = "usage: %prog [options]"
 	parser = OptionParser(usage, version="%prog dev-unreleased")
	parser.add_option("-i", "--dab-file", dest="dab", help="DAB file", metavar="FILE")
	parser.add_option("-o", "--output-file", dest="out", help="Output file (DAT or PCL)", metavar="FILE")
 
	(options, args) = parser.parse_args()

    	if options.dab is None:
        	sys.stderr.write("--dab file is required.\n")
        	sys.exit()
	if options.out is not None and not options.out.endswith('.pcl') and not options.out.endswith('.dat'):
		sys.stderr.write("Unknown file format for: " + options.out + "\n")
		sys.exit()

	dab = dat(options.dab)

	if options.out is None:
		dab.print_table()
	else:
		ofile = open(options.out, 'w')
		if options.out.endswith('.pcl'):
			dab.print_table(ofile)
		elif options.out.endswith('.dat'):
			dab.print_flat(ofile)
		ofile.close()
